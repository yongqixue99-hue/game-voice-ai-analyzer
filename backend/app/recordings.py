from __future__ import annotations

import logging
import mimetypes
import re
import shutil
import subprocess
import wave
from datetime import timezone
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import get_settings
from .database import get_db
from .models import Recording

router = APIRouter(prefix="/api/recordings", tags=["recordings"])
settings = get_settings()
logger = logging.getLogger(__name__)


def serialize_recording(recording: Recording) -> dict[str, object]:
    created_at = recording.created_at
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)

    return {
        "id": recording.id,
        "filename": recording.filename,
        "original_filename": recording.original_filename,
        "file_path": recording.file_path,
        "mime_type": recording.mime_type,
        "size_bytes": recording.size_bytes,
        "duration": recording.duration,
        "status": recording.status,
        "created_at": created_at.isoformat(),
    }


def resolve_recording_path(recording: Recording) -> Path:
    file_path = Path(recording.file_path)
    if file_path.is_absolute():
        return file_path
    return settings.project_root / file_path


def validate_upload_metadata(file: UploadFile) -> tuple[str, str]:
    original_filename = Path(file.filename or "").name
    if not original_filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请上传带文件名的音频文件。",
        )

    suffix = Path(original_filename).suffix.lower()
    if suffix not in settings.allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="仅支持 mp3、wav、m4a、webm 音频文件。",
        )

    guessed_mime_type = mimetypes.guess_type(original_filename)[0]
    raw_mime_type = file.content_type or guessed_mime_type or "application/octet-stream"
    mime_type = raw_mime_type.split(";", 1)[0].strip().lower()
    if (
        mime_type not in settings.allowed_mime_types
        and mime_type != "application/octet-stream"
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="上传文件类型不是受支持的音频格式。",
        )

    if mime_type == "application/octet-stream" and guessed_mime_type:
        mime_type = guessed_mime_type

    return original_filename, mime_type


async def save_upload_file(file: UploadFile, destination: Path) -> int:
    total_bytes = 0
    destination.parent.mkdir(parents=True, exist_ok=True)

    try:
        with destination.open("wb") as output:
            while chunk := await file.read(1024 * 1024):
                total_bytes += len(chunk)
                if total_bytes > settings.max_upload_bytes:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="上传文件超过大小限制。",
                    )
                output.write(chunk)
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    finally:
        await file.close()

    if total_bytes == 0:
        destination.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能上传空音频文件。",
        )

    return total_bytes


def detect_audio_duration_seconds(audio_path: Path) -> float | None:
    """Best-effort duration probe without adding heavyweight media deps."""

    try:
        if audio_path.suffix.lower() == ".wav":
            with wave.open(str(audio_path), "rb") as wav_file:
                frame_rate = wav_file.getframerate()
                if frame_rate > 0:
                    duration = wav_file.getnframes() / frame_rate
                    return duration if duration > 0 else None
    except (wave.Error, OSError, EOFError) as error:
        logger.debug("Could not read WAV duration for %s: %s", audio_path, error)

    afinfo = shutil.which("afinfo")
    if afinfo is None:
        return None

    try:
        result = subprocess.run(
            [afinfo, str(audio_path)],
            capture_output=True,
            check=False,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        logger.debug("Could not run afinfo for %s: %s", audio_path, error)
        return None

    if result.returncode != 0:
        logger.debug("afinfo failed for %s: %s", audio_path, result.stderr[:500])
        return None

    match = re.search(r"estimated duration:\s*([0-9.]+)\s*sec", result.stdout)
    if match is None:
        return None

    try:
        duration = float(match.group(1))
    except ValueError:
        return None
    return duration if duration > 0 else None


async def create_recording_from_upload(file: UploadFile, db: Session) -> Recording:
    original_filename, mime_type = validate_upload_metadata(file)
    suffix = Path(original_filename).suffix.lower()
    stored_filename = f"{uuid4().hex}{suffix}"
    destination = settings.audio_storage_dir / stored_filename

    size_bytes = await save_upload_file(file, destination)
    try:
        relative_path = destination.relative_to(settings.project_root)
    except ValueError:
        relative_path = destination

    recording = Recording(
        filename=stored_filename,
        original_filename=original_filename,
        file_path=str(relative_path),
        mime_type=mime_type,
        size_bytes=size_bytes,
        duration=detect_audio_duration_seconds(destination),
        status="uploaded",
    )

    try:
        db.add(recording)
        db.commit()
        db.refresh(recording)
    except Exception:
        db.rollback()
        destination.unlink(missing_ok=True)
        raise

    return recording


@router.post("", status_code=status.HTTP_201_CREATED)
@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_recording(
    file: UploadFile = File(...), db: Session = Depends(get_db)
) -> dict[str, object]:
    recording = await create_recording_from_upload(file, db)
    return serialize_recording(recording)


@router.get("")
def list_recordings(db: Session = Depends(get_db)) -> list[dict[str, object]]:
    recordings = db.scalars(
        select(Recording).order_by(Recording.created_at.desc())
    ).all()
    return [serialize_recording(recording) for recording in recordings]


@router.get("/{recording_id}")
def get_recording(
    recording_id: str, db: Session = Depends(get_db)
) -> dict[str, object]:
    recording = db.get(Recording, recording_id)
    if recording is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="录音不存在。"
        )
    return serialize_recording(recording)


@router.get("/{recording_id}/audio")
def get_recording_audio(recording_id: str, db: Session = Depends(get_db)) -> FileResponse:
    recording = db.get(Recording, recording_id)
    if recording is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="录音不存在。"
        )

    audio_path = resolve_recording_path(recording)
    if not audio_path.exists() or not audio_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="录音文件不存在。"
        )

    return FileResponse(
        audio_path,
        media_type=recording.mime_type,
        filename=recording.original_filename,
    )
