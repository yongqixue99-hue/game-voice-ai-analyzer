from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from .config import get_settings
from .database import get_db
from .llm import (
    LLMProviderError,
    generic_mock_summary_payload,
    get_llm_provider,
    normalize_saved_analysis_payload,
)
from .models import Recording, RecordingAnalysis, TranscriptSegment
from .models import SpeakerLabel
from .segments import get_speaker_label_map
from .session_summaries import mark_session_summaries_stale_for_recording

router = APIRouter(prefix="/api/recordings", tags=["analyses"])


def ensure_timezone(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def get_latest_transcript_update(recording_id: str, db: Session) -> datetime | None:
    return db.scalar(
        select(func.max(TranscriptSegment.updated_at)).where(
            TranscriptSegment.recording_id == recording_id
        )
    )


def get_latest_speaker_label_update(recording_id: str, db: Session) -> datetime | None:
    return db.scalar(
        select(func.max(SpeakerLabel.updated_at)).where(
            SpeakerLabel.recording_id == recording_id
        )
    )


def is_analysis_stale(analysis: RecordingAnalysis, db: Session) -> bool:
    analysis_updated_at = ensure_timezone(analysis.updated_at)
    for changed_at in (
        get_latest_transcript_update(analysis.recording_id, db),
        get_latest_speaker_label_update(analysis.recording_id, db),
    ):
        if changed_at is not None and ensure_timezone(changed_at) > analysis_updated_at:
            return True
    return False


def serialize_analysis(analysis: RecordingAnalysis, db: Session) -> dict[str, Any]:
    created_at = analysis.created_at
    updated_at = analysis.updated_at
    created_at = ensure_timezone(created_at)
    updated_at = ensure_timezone(updated_at)

    raw_payload = json.loads(analysis.analysis_json)
    if analysis.model == "mock-review-v1":
        raw_payload = generic_mock_summary_payload(
            "当前为旧版 mock 结果，不代表真实内容分析；重新生成后会刷新为新版 AI 总结。"
        )
    payload = normalize_saved_analysis_payload(raw_payload)
    return {
        "id": analysis.id,
        "recording_id": analysis.recording_id,
        "provider": analysis.provider,
        "model": analysis.model,
        **payload,
        "is_stale": is_analysis_stale(analysis, db),
        "created_at": created_at.isoformat(),
        "updated_at": updated_at.isoformat(),
    }


def get_recording_or_404(recording_id: str, db: Session) -> Recording:
    recording = db.get(Recording, recording_id)
    if recording is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="录音不存在。",
        )
    return recording


def get_latest_analysis(
    recording_id: str, db: Session
) -> RecordingAnalysis | None:
    return db.scalars(
        select(RecordingAnalysis)
        .where(RecordingAnalysis.recording_id == recording_id)
        .order_by(RecordingAnalysis.updated_at.desc(), RecordingAnalysis.created_at.desc())
    ).first()


@router.get("/{recording_id}/analysis")
def get_recording_analysis(
    recording_id: str, db: Session = Depends(get_db)
) -> dict[str, Any]:
    get_recording_or_404(recording_id, db)
    analysis = get_latest_analysis(recording_id, db)
    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="暂无 AI 总结结果。",
        )
    return serialize_analysis(analysis, db)


@router.post("/{recording_id}/analyze", status_code=status.HTTP_201_CREATED)
def analyze_recording(
    recording_id: str, db: Session = Depends(get_db)
) -> dict[str, Any]:
    recording = get_recording_or_404(recording_id, db)
    segments = db.scalars(
        select(TranscriptSegment)
        .where(TranscriptSegment.recording_id == recording.id)
        .order_by(TranscriptSegment.start_time.asc(), TranscriptSegment.end_time.asc())
    ).all()

    if not segments:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先完成转写，再生成 AI 总结。",
        )

    speaker_label_map = get_speaker_label_map(recording.id, db)
    provider = get_llm_provider(get_settings())
    try:
        result = provider.analyze(list(segments), speaker_label_map)
    except LLMProviderError as error:
        raise HTTPException(
            status_code=error.status_code,
            detail=error.detail,
        ) from error

    analysis = RecordingAnalysis(
        recording_id=recording.id,
        provider=result.provider,
        model=result.model,
        analysis_json=json.dumps(result.analysis, ensure_ascii=False),
        raw_response_json=json.dumps(result.raw_response, ensure_ascii=False),
    )

    try:
        db.execute(
            delete(RecordingAnalysis).where(
                RecordingAnalysis.recording_id == recording.id
            )
        )
        db.add(analysis)
        mark_session_summaries_stale_for_recording(recording.id, db)
        db.commit()
        db.refresh(analysis)
    except Exception:
        db.rollback()
        raise

    return serialize_analysis(analysis, db)
