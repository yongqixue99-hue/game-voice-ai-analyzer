from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from .config import get_settings
from .database import get_db
from .llm import (
    LLMProviderError,
    get_llm_provider,
    normalize_saved_analysis_payload,
    normalize_saved_session_summary_payload,
)
from .models import (
    Recording,
    RecordingAnalysis,
    RecordingSessionChunk,
    RecordingSessionSummary,
    SpeakerLabel,
    TranscriptSegment,
    utc_now,
)
from .recording_sessions import (
    get_existing_session,
    get_session_chunks,
    serialize_datetime,
)

router = APIRouter(
    prefix="/api/recording-sessions",
    tags=["recording-session-summaries"],
)


def get_latest_session_summary(
    session_id: str, db: Session
) -> RecordingSessionSummary | None:
    return db.scalars(
        select(RecordingSessionSummary)
        .where(RecordingSessionSummary.session_id == session_id)
        .order_by(
            RecordingSessionSummary.updated_at.desc(),
            RecordingSessionSummary.created_at.desc(),
        )
    ).first()


def serialize_session_summary(summary: RecordingSessionSummary) -> dict[str, Any]:
    payload = normalize_saved_session_summary_payload(json.loads(summary.summary_json))
    return {
        "id": summary.id,
        "session_id": summary.session_id,
        "provider": summary.provider,
        "model": summary.model,
        **payload,
        "is_stale": summary.is_stale,
        "created_at": serialize_datetime(summary.created_at),
        "updated_at": serialize_datetime(summary.updated_at),
    }


def mark_session_summaries_stale_for_recording(
    recording_id: str, db: Session
) -> None:
    session_ids = db.scalars(
        select(RecordingSessionChunk.session_id).where(
            RecordingSessionChunk.recording_id == recording_id
        )
    ).all()
    if not session_ids:
        return

    summaries = db.scalars(
        select(RecordingSessionSummary).where(
            RecordingSessionSummary.session_id.in_(session_ids),
            RecordingSessionSummary.is_stale.is_(False),
        )
    ).all()
    for summary in summaries:
        summary.is_stale = True
        summary.updated_at = utc_now()


def get_speaker_label_map(recording_id: str, db: Session) -> dict[str, str]:
    labels = db.scalars(
        select(SpeakerLabel).where(
            SpeakerLabel.recording_id == recording_id,
            SpeakerLabel.display_name != "",
        )
    ).all()
    return {label.source_label: label.display_name for label in labels}


def get_latest_recording_analysis(
    recording_id: str, db: Session
) -> RecordingAnalysis | None:
    return db.scalars(
        select(RecordingAnalysis)
        .where(RecordingAnalysis.recording_id == recording_id)
        .order_by(RecordingAnalysis.updated_at.desc(), RecordingAnalysis.created_at.desc())
    ).first()


def build_chunk_transcript(
    chunk: RecordingSessionChunk,
    segments: list[TranscriptSegment],
    speaker_label_map: dict[str, str],
) -> str:
    lines: list[str] = []
    for segment in segments:
        display_label = speaker_label_map.get(segment.speaker_label)
        speaker_label = (
            f"{display_label} ({segment.speaker_label})"
            if display_label and display_label != segment.speaker_label
            else segment.speaker_label
        )
        session_start = chunk.start_offset_seconds + segment.start_time
        session_end = chunk.start_offset_seconds + segment.end_time
        lines.append(
            f"[{session_start:.2f}-{session_end:.2f}] {speaker_label}: {segment.text}"
        )
    return "\n".join(lines)


def build_session_summary_context(
    session_id: str, db: Session
) -> tuple[list[dict[str, Any]], list[str]]:
    chunks = get_session_chunks(session_id, db)
    if not chunks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该长录音会话暂无 chunks，无法生成整场总结。",
        )

    context_chunks: list[dict[str, Any]] = []
    notes: list[str] = []
    chunks_with_transcript = 0

    for chunk in chunks:
        recording = db.get(Recording, chunk.recording_id) if chunk.recording_id else None
        if recording is None:
            notes.append(f"第 {chunk.chunk_index} 段缺少关联录音。")
            context_chunks.append(
                {
                    "chunk_index": chunk.chunk_index,
                    "start_time": chunk.start_offset_seconds,
                    "end_time": chunk.end_offset_seconds,
                    "recording_filename": "",
                    "transcript": "",
                    "analysis_summary": "",
                    "analysis_key_points": [],
                }
            )
            continue

        segments = db.scalars(
            select(TranscriptSegment)
            .where(TranscriptSegment.recording_id == recording.id)
            .order_by(TranscriptSegment.start_time.asc(), TranscriptSegment.end_time.asc())
        ).all()
        if segments:
            chunks_with_transcript += 1
        else:
            notes.append(f"第 {chunk.chunk_index} 段缺少转写。")

        recording_analysis = get_latest_recording_analysis(recording.id, db)
        analysis_payload: dict[str, Any] = {}
        if recording_analysis is None:
            notes.append(f"第 {chunk.chunk_index} 段缺少分段 AI 总结。")
        else:
            analysis_payload = normalize_saved_analysis_payload(
                json.loads(recording_analysis.analysis_json)
            )

        speaker_label_map = get_speaker_label_map(recording.id, db)
        context_chunks.append(
            {
                "chunk_index": chunk.chunk_index,
                "start_time": chunk.start_offset_seconds,
                "end_time": chunk.end_offset_seconds,
                "recording_filename": recording.original_filename,
                "transcript": build_chunk_transcript(chunk, list(segments), speaker_label_map),
                "analysis_summary": analysis_payload.get("summary", ""),
                "analysis_key_points": analysis_payload.get("key_points", []),
            }
        )

    if chunks_with_transcript == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先完成至少一个 chunk 转写，再生成整场总结。",
        )

    return context_chunks, notes


def append_context_notes(payload: dict[str, Any], notes: list[str]) -> dict[str, Any]:
    if not notes:
        return payload
    existing_notes = payload.get("notes")
    if not isinstance(existing_notes, list):
        existing_notes = []
    merged_notes: list[str] = []
    for note in [*notes, *existing_notes]:
        text = str(note).strip()
        if text and text not in merged_notes:
            merged_notes.append(text)
    return {**payload, "notes": merged_notes}


@router.post("/{session_id}/summary", status_code=status.HTTP_201_CREATED)
def generate_recording_session_summary(
    session_id: str, db: Session = Depends(get_db)
) -> dict[str, Any]:
    get_existing_session(session_id, db)
    context_chunks, context_notes = build_session_summary_context(session_id, db)

    provider = get_llm_provider(get_settings())
    try:
        result = provider.summarize_session(context_chunks)
    except LLMProviderError as error:
        raise HTTPException(
            status_code=error.status_code,
            detail=error.detail,
        ) from error

    summary_payload = append_context_notes(result.analysis, context_notes)
    summary_payload = normalize_saved_session_summary_payload(summary_payload)
    summary = RecordingSessionSummary(
        session_id=session_id,
        provider=result.provider,
        model=result.model,
        summary_json=json.dumps(summary_payload, ensure_ascii=False),
        raw_response_json=json.dumps(result.raw_response, ensure_ascii=False),
        is_stale=False,
    )

    try:
        db.execute(
            delete(RecordingSessionSummary).where(
                RecordingSessionSummary.session_id == session_id
            )
        )
        db.add(summary)
        db.commit()
        db.refresh(summary)
    except Exception:
        db.rollback()
        raise

    return serialize_session_summary(summary)


@router.get("/{session_id}/summary")
def get_recording_session_summary(
    session_id: str, db: Session = Depends(get_db)
) -> dict[str, Any]:
    get_existing_session(session_id, db)
    summary = get_latest_session_summary(session_id, db)
    if summary is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="暂无整场总结结果。",
        )
    return serialize_session_summary(summary)


@router.get("/{session_id}/export.md")
def export_recording_session_summary_markdown(
    session_id: str, db: Session = Depends(get_db)
) -> Response:
    get_existing_session(session_id, db)
    summary = get_latest_session_summary(session_id, db)
    if summary is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="暂无整场总结结果，无法导出。",
        )
    content = render_session_summary_markdown(serialize_session_summary(summary))
    return Response(
        content=content,
        media_type="text/markdown; charset=utf-8",
        headers={
            "Content-Disposition": 'attachment; filename="recording-session-summary.md"'
        },
    )


@router.get("/{session_id}/export.txt")
def export_recording_session_summary_text(
    session_id: str, db: Session = Depends(get_db)
) -> Response:
    get_existing_session(session_id, db)
    summary = get_latest_session_summary(session_id, db)
    if summary is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="暂无整场总结结果，无法导出。",
        )
    content = render_session_summary_text(serialize_session_summary(summary))
    return Response(
        content=content,
        media_type="text/plain; charset=utf-8",
        headers={
            "Content-Disposition": 'attachment; filename="recording-session-summary.txt"'
        },
    )


def render_session_summary_markdown(summary: dict[str, Any]) -> str:
    lines = [
        f"# {summary['title']}",
        "",
        "## 整体总结",
        "",
        summary["summary"],
        "",
        "## 重点信息",
        "",
    ]
    key_points = summary.get("key_points") or []
    lines.extend([f"- {item}" for item in key_points] or ["- 无"])
    lines.extend(["", "## 时间线", ""])
    timeline = summary.get("timeline") or []
    lines.extend(
        [
            (
                f"- {format_seconds(item['start_time'])} - {format_seconds(item['end_time'])} "
                f"{item['title']}：{item['summary']}"
            )
            for item in timeline
        ]
        or ["- 无"]
    )
    lines.extend(["", "## 分段摘要", ""])
    chunk_summaries = summary.get("chunk_summaries") or []
    lines.extend(
        [
            (
                f"- Chunk {item['chunk_index']} "
                f"({format_seconds(item['start_time'])} - {format_seconds(item['end_time'])})："
                f"{item['summary']}"
            )
            for item in chunk_summaries
        ]
        or ["- 无"]
    )
    lines.extend(["", "## 备注", ""])
    notes = summary.get("notes") or []
    lines.extend([f"- {item}" for item in notes] or ["- 无"])
    lines.extend(
        [
            "",
            "## 生成信息",
            "",
            f"- provider: {summary['provider']}",
            f"- model: {summary['model']}",
            f"- generated_at: {summary['updated_at']}",
        ]
    )
    return "\n".join(lines) + "\n"


def render_session_summary_text(summary: dict[str, Any]) -> str:
    markdown = render_session_summary_markdown(summary)
    text = markdown.replace("# ", "").replace("## ", "")
    return text.replace("- ", "")


def format_seconds(value: float) -> str:
    total_seconds = max(0, int(value))
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes:02d}:{seconds:02d}"
