from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete
from sqlalchemy.orm import Session

from .asr import (
    ASRProviderError,
    ASRSegment,
    build_public_audio_url,
    get_asr_provider,
)
from .config import get_settings
from .database import get_db
from .models import Recording, TranscriptSegment
from .recordings import resolve_recording_path
from .segments import serialize_segment
from .session_summaries import mark_session_summaries_stale_for_recording

router = APIRouter(prefix="/api/recordings", tags=["transcriptions"])


def persist_asr_segments(
    recording: Recording, asr_segments: list[ASRSegment], db: Session
) -> list[TranscriptSegment]:
    if not asr_segments:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="转写结果为空，无法生成时间轴。",
        )

    segments = [
        TranscriptSegment(
            recording_id=recording.id,
            speaker_label=segment.speaker_label,
            start_time=segment.start_time,
            end_time=segment.end_time,
            text=segment.text,
            source=segment.source,
        )
        for segment in asr_segments
    ]

    try:
        db.execute(
            delete(TranscriptSegment).where(
                TranscriptSegment.recording_id == recording.id,
                TranscriptSegment.source.in_(("mock", "aliyun")),
            )
        )
        db.add_all(segments)
        mark_session_summaries_stale_for_recording(recording.id, db)
        db.commit()
    except Exception:
        db.rollback()
        raise

    for segment in segments:
        db.refresh(segment)

    return sorted(segments, key=lambda segment: (segment.start_time, segment.end_time))


@router.post("/{recording_id}/transcribe", status_code=status.HTTP_201_CREATED)
def transcribe_recording(
    recording_id: str, db: Session = Depends(get_db)
) -> list[dict[str, object]]:
    recording = db.get(Recording, recording_id)
    if recording is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="录音不存在。",
        )

    audio_path = resolve_recording_path(recording)
    if not audio_path.exists() or not audio_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="录音文件不存在。",
        )

    settings = get_settings()
    public_audio_url = build_public_audio_url(settings, recording.id)
    provider = get_asr_provider(settings)

    try:
        asr_segments = provider.transcribe(recording, public_audio_url)
    except ASRProviderError as error:
        raise HTTPException(
            status_code=error.status_code,
            detail=error.detail,
        ) from error

    segments = persist_asr_segments(recording, asr_segments, db)
    return [serialize_segment(segment) for segment in segments]
