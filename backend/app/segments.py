from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from .database import get_db
from .models import Recording, SpeakerLabel, TranscriptSegment, utc_now
from .session_summaries import mark_session_summaries_stale_for_recording

router = APIRouter(prefix="/api/recordings", tags=["segments"])

MOCK_SEGMENTS = (
    (0.0, 3.0, "Speaker 1", "兄弟们这波可以打"),
    (3.0, 7.0, "Speaker 2", "别急，对面打野不见了"),
    (7.0, 12.0, "Speaker 1", "我有大，我先开"),
    (12.0, 18.0, "Speaker 3", "我绕后了，等我位置"),
    (18.0, 24.0, "Speaker 2", "可以可以，直接开"),
)


class SegmentUpdateRequest(BaseModel):
    text: str


class SpeakerLabelUpdateRequest(BaseModel):
    source_label: str
    display_name: str


def ensure_timezone(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def get_speaker_label_map(recording_id: str, db: Session) -> dict[str, str]:
    labels = db.scalars(
        select(SpeakerLabel).where(
            SpeakerLabel.recording_id == recording_id,
            SpeakerLabel.display_name != "",
        )
    ).all()
    return {label.source_label: label.display_name for label in labels}


def serialize_segment(
    segment: TranscriptSegment,
    speaker_label_map: dict[str, str] | None = None,
) -> dict[str, object]:
    created_at = segment.created_at
    updated_at = segment.updated_at
    created_at = ensure_timezone(created_at)
    updated_at = ensure_timezone(updated_at)

    resolved_label_map = speaker_label_map or {}
    display_speaker_label = resolved_label_map.get(
        segment.speaker_label, segment.speaker_label
    )

    return {
        "id": segment.id,
        "recording_id": segment.recording_id,
        "speaker_label": segment.speaker_label,
        "display_speaker_label": display_speaker_label,
        "start_time": segment.start_time,
        "end_time": segment.end_time,
        "text": segment.text,
        "source": segment.source,
        "is_edited": segment.is_edited,
        "created_at": created_at.isoformat(),
        "updated_at": updated_at.isoformat(),
    }


def get_existing_recording(recording_id: str, db: Session) -> Recording:
    recording = db.get(Recording, recording_id)
    if recording is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="录音不存在。",
        )
    return recording


def build_mock_segments(recording: Recording) -> list[TranscriptSegment]:
    segments: list[TranscriptSegment] = []
    duration = recording.duration

    for start_time, end_time, speaker_label, text in MOCK_SEGMENTS:
        if duration is not None:
            if start_time >= duration:
                continue
            end_time = min(end_time, duration)
            if end_time <= start_time:
                continue

        segments.append(
            TranscriptSegment(
                recording_id=recording.id,
                speaker_label=speaker_label,
                start_time=start_time,
                end_time=end_time,
                text=text,
                source="mock",
            )
        )

    return segments


@router.get("/{recording_id}/segments")
def list_segments(
    recording_id: str, db: Session = Depends(get_db)
) -> list[dict[str, object]]:
    get_existing_recording(recording_id, db)
    speaker_label_map = get_speaker_label_map(recording_id, db)
    segments = db.scalars(
        select(TranscriptSegment)
        .where(TranscriptSegment.recording_id == recording_id)
        .order_by(TranscriptSegment.start_time.asc(), TranscriptSegment.created_at.asc())
    ).all()
    return [serialize_segment(segment, speaker_label_map) for segment in segments]


@router.patch("/{recording_id}/segments/{segment_id}")
def update_segment(
    recording_id: str,
    segment_id: str,
    request: SegmentUpdateRequest,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    get_existing_recording(recording_id, db)
    segment = db.scalars(
        select(TranscriptSegment).where(
            TranscriptSegment.id == segment_id,
            TranscriptSegment.recording_id == recording_id,
        )
    ).first()
    if segment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="转写片段不存在。",
        )

    next_text = request.text.strip()
    if not next_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="转写文本不能为空。",
        )
    if len(next_text) > 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="转写文本不能超过 1000 个字符。",
        )

    segment.text = next_text
    segment.is_edited = True
    segment.updated_at = utc_now()
    mark_session_summaries_stale_for_recording(recording_id, db)
    db.commit()
    db.refresh(segment)

    return serialize_segment(segment, get_speaker_label_map(recording_id, db))


@router.post("/{recording_id}/segments/mock", status_code=status.HTTP_201_CREATED)
def generate_mock_segments(
    recording_id: str, db: Session = Depends(get_db)
) -> list[dict[str, object]]:
    recording = get_existing_recording(recording_id, db)

    db.execute(
        delete(TranscriptSegment).where(TranscriptSegment.recording_id == recording_id)
    )
    segments = build_mock_segments(recording)
    db.add_all(segments)
    db.commit()

    for segment in segments:
        db.refresh(segment)

    speaker_label_map = get_speaker_label_map(recording_id, db)
    segments.sort(key=lambda segment: segment.start_time)
    return [serialize_segment(segment, speaker_label_map) for segment in segments]


def get_existing_source_labels(recording_id: str, db: Session) -> dict[str, int]:
    rows = db.execute(
        select(TranscriptSegment.speaker_label, func.count(TranscriptSegment.id))
        .where(TranscriptSegment.recording_id == recording_id)
        .group_by(TranscriptSegment.speaker_label)
    ).all()
    return {str(source_label): int(count) for source_label, count in rows}


def serialize_speaker_label(
    source_label: str,
    segment_count: int,
    label: SpeakerLabel | None,
) -> dict[str, Any]:
    display_name = label.display_name if label and label.display_name else source_label
    created_at = ensure_timezone(label.created_at).isoformat() if label else None
    updated_at = ensure_timezone(label.updated_at).isoformat() if label else None
    return {
        "source_label": source_label,
        "display_name": display_name,
        "segment_count": segment_count,
        "created_at": created_at,
        "updated_at": updated_at,
    }


@router.get("/{recording_id}/speaker-labels")
def list_speaker_labels(
    recording_id: str, db: Session = Depends(get_db)
) -> list[dict[str, Any]]:
    get_existing_recording(recording_id, db)
    counts_by_source_label = get_existing_source_labels(recording_id, db)
    labels = db.scalars(
        select(SpeakerLabel).where(SpeakerLabel.recording_id == recording_id)
    ).all()
    labels_by_source = {label.source_label: label for label in labels}

    return [
        serialize_speaker_label(
            source_label,
            counts_by_source_label[source_label],
            labels_by_source.get(source_label),
        )
        for source_label in sorted(counts_by_source_label)
    ]


@router.patch("/{recording_id}/speaker-labels")
def update_speaker_label(
    recording_id: str,
    request: SpeakerLabelUpdateRequest,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    get_existing_recording(recording_id, db)

    source_label = request.source_label.strip()
    display_name = request.display_name.strip()
    if not source_label:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="source_label 不能为空。",
        )
    if len(display_name) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="显示名称不能超过 100 个字符。",
        )

    counts_by_source_label = get_existing_source_labels(recording_id, db)
    if source_label not in counts_by_source_label:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="该 speaker/channel 不存在。",
        )

    label = db.scalars(
        select(SpeakerLabel).where(
            SpeakerLabel.recording_id == recording_id,
            SpeakerLabel.source_label == source_label,
        )
    ).first()
    if label is None:
        label = SpeakerLabel(
            recording_id=recording_id,
            source_label=source_label,
            display_name=display_name,
        )
        db.add(label)
    else:
        label.display_name = display_name
        label.updated_at = utc_now()

    mark_session_summaries_stale_for_recording(recording_id, db)
    db.commit()
    db.refresh(label)

    return serialize_speaker_label(
        source_label,
        counts_by_source_label[source_label],
        label,
    )
