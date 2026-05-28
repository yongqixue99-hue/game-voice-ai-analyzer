from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import get_db
from .models import RecordingSession, RecordingSessionChunk, utc_now
from .recordings import create_recording_from_upload, serialize_recording

router = APIRouter(prefix="/api/recording-sessions", tags=["recording-sessions"])

ALLOWED_CHUNK_DURATIONS_SECONDS = {30, 60, 180, 300}
SESSION_STATUSES = {"recording", "stopping", "completed", "failed"}
CHUNK_STATUSES = {
    "recording",
    "uploading",
    "uploaded",
    "transcribing",
    "transcribed",
    "summarizing",
    "completed",
    "failed",
}


class CreateRecordingSessionRequest(BaseModel):
    title: str | None = None
    chunk_duration_seconds: int = Field(..., gt=0)


class UpdateRecordingSessionRequest(BaseModel):
    status: str | None = None
    stopped_at: datetime | None = None


class UpdateRecordingSessionChunkRequest(BaseModel):
    status: str | None = None
    error_message: str | None = None


def serialize_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()


def get_existing_session(session_id: str, db: Session) -> RecordingSession:
    session = db.get(RecordingSession, session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="长录音会话不存在。",
        )
    return session


def serialize_session(
    session: RecordingSession,
    chunks: list[RecordingSessionChunk] | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "id": session.id,
        "title": session.title,
        "status": session.status,
        "chunk_duration_seconds": session.chunk_duration_seconds,
        "started_at": serialize_datetime(session.started_at),
        "stopped_at": serialize_datetime(session.stopped_at),
        "created_at": serialize_datetime(session.created_at),
        "updated_at": serialize_datetime(session.updated_at),
    }
    if chunks is not None:
        payload["chunks"] = [serialize_chunk(chunk) for chunk in chunks]
    return payload


def serialize_chunk(chunk: RecordingSessionChunk) -> dict[str, object]:
    recording = getattr(chunk, "recording", None)
    return {
        "id": chunk.id,
        "session_id": chunk.session_id,
        "recording_id": chunk.recording_id,
        "chunk_index": chunk.chunk_index,
        "start_offset_seconds": chunk.start_offset_seconds,
        "end_offset_seconds": chunk.end_offset_seconds,
        "status": chunk.status,
        "error_message": chunk.error_message,
        "recording": serialize_recording(recording) if recording else None,
        "created_at": serialize_datetime(chunk.created_at),
        "updated_at": serialize_datetime(chunk.updated_at),
    }


def get_session_chunks(session_id: str, db: Session) -> list[RecordingSessionChunk]:
    return db.scalars(
        select(RecordingSessionChunk)
        .where(RecordingSessionChunk.session_id == session_id)
        .order_by(RecordingSessionChunk.chunk_index.asc())
    ).all()


@router.post("", status_code=status.HTTP_201_CREATED)
def create_recording_session(
    request: CreateRecordingSessionRequest, db: Session = Depends(get_db)
) -> dict[str, object]:
    if request.chunk_duration_seconds not in ALLOWED_CHUNK_DURATIONS_SECONDS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="分段时长仅支持 30 秒、1 分钟、3 分钟或 5 分钟。",
        )

    now = utc_now()
    title = request.title.strip() if request.title else ""
    session = RecordingSession(
        title=title or f"长录音 {now.strftime('%Y-%m-%d %H:%M:%S')}",
        status="recording",
        chunk_duration_seconds=request.chunk_duration_seconds,
        started_at=now,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return serialize_session(session, [])


@router.get("")
def list_recording_sessions(db: Session = Depends(get_db)) -> list[dict[str, object]]:
    sessions = db.scalars(
        select(RecordingSession).order_by(RecordingSession.created_at.desc())
    ).all()
    return [
        serialize_session(session, get_session_chunks(session.id, db))
        for session in sessions
    ]


@router.get("/{session_id}")
def get_recording_session(
    session_id: str, db: Session = Depends(get_db)
) -> dict[str, object]:
    session = get_existing_session(session_id, db)
    return serialize_session(session, get_session_chunks(session.id, db))


@router.patch("/{session_id}")
def update_recording_session(
    session_id: str,
    request: UpdateRecordingSessionRequest,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    session = get_existing_session(session_id, db)
    if request.status is not None:
        if request.status not in SESSION_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="长录音会话状态不合法。",
            )
        session.status = request.status

    if request.stopped_at is not None:
        session.stopped_at = request.stopped_at
    elif request.status in {"completed", "failed"} and session.stopped_at is None:
        session.stopped_at = utc_now()

    session.updated_at = utc_now()
    db.commit()
    db.refresh(session)
    return serialize_session(session, get_session_chunks(session.id, db))


@router.post("/{session_id}/chunks", status_code=status.HTTP_201_CREATED)
async def upload_recording_session_chunk(
    session_id: str,
    chunk_index: int = Form(...),
    start_offset_seconds: float = Form(...),
    end_offset_seconds: float = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    get_existing_session(session_id, db)
    if chunk_index < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="chunk_index 必须从 1 开始。",
        )
    if start_offset_seconds < 0 or end_offset_seconds <= start_offset_seconds:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="chunk 时间范围不合法。",
        )

    existing = db.scalars(
        select(RecordingSessionChunk).where(
            RecordingSessionChunk.session_id == session_id,
            RecordingSessionChunk.chunk_index == chunk_index,
        )
    ).first()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="该 chunk 序号已经存在。",
        )

    recording = await create_recording_from_upload(file, db)
    chunk = RecordingSessionChunk(
        session_id=session_id,
        recording_id=recording.id,
        chunk_index=chunk_index,
        start_offset_seconds=start_offset_seconds,
        end_offset_seconds=end_offset_seconds,
        status="uploaded",
    )
    db.add(chunk)
    db.commit()
    db.refresh(chunk)
    setattr(chunk, "recording", recording)
    return serialize_chunk(chunk)


@router.patch("/{session_id}/chunks/{chunk_id}")
def update_recording_session_chunk(
    session_id: str,
    chunk_id: str,
    request: UpdateRecordingSessionChunkRequest,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    get_existing_session(session_id, db)
    chunk = db.scalars(
        select(RecordingSessionChunk).where(
            RecordingSessionChunk.id == chunk_id,
            RecordingSessionChunk.session_id == session_id,
        )
    ).first()
    if chunk is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="长录音 chunk 不存在。",
        )

    if request.status is not None:
        if request.status not in CHUNK_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="chunk 状态不合法。",
            )
        chunk.status = request.status

    chunk.error_message = request.error_message
    chunk.updated_at = utc_now()
    db.commit()
    db.refresh(chunk)
    return serialize_chunk(chunk)
