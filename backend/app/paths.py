"""Centralized data-path resolution for the backend.

Resolution priority (designed so existing Web/Tauri *dev* behavior is unchanged):

1. Explicit env (`DATABASE_URL` / `AUDIO_STORAGE_DIR`) — highest, used verbatim.
2. `LUNARIS_DATA_DIR` — desktop data root; derives db/audio/exports/logs/config.
3. Source-tree relative paths — the historical dev layout
   (`backend/recordings.sqlite3`, `storage/audio`).

`LUNARIS_DATA_DIR` layout::

    LUNARIS_DATA_DIR/
      lunaris.sqlite3
      audio/
      exports/
      logs/
      config/

We never migrate existing data: when `LUNARIS_DATA_DIR` is set we point at a
fresh DB/audio under that root and leave the in-repo files untouched.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DataPaths:
    """Resolved data locations the backend should read/write."""

    project_root: Path
    data_dir: Path | None
    database_url: str
    audio_storage_dir: Path
    exports_dir: Path
    logs_dir: Path
    config_dir: Path


def _data_dir_from_env() -> Path | None:
    raw = os.getenv("LUNARIS_DATA_DIR")
    if raw and raw.strip():
        return Path(raw.strip()).expanduser()
    return None


def resolve_data_paths(project_root: Path) -> DataPaths:
    """Resolve all data paths from env, falling back to the source-tree layout."""

    data_dir = _data_dir_from_env()

    if data_dir is not None:
        default_db_url = f"sqlite:///{data_dir / 'lunaris.sqlite3'}"
        default_audio = data_dir / "audio"
        exports_dir = data_dir / "exports"
        logs_dir = data_dir / "logs"
        config_dir = data_dir / "config"
    else:
        default_db_url = f"sqlite:///{project_root / 'backend' / 'recordings.sqlite3'}"
        default_audio = project_root / "storage" / "audio"
        # Dev fallback: keep ancillary dirs inside the repo tree, no behavior change
        # for db/audio which retain their historical locations.
        exports_dir = project_root / "storage" / "exports"
        logs_dir = project_root / "storage" / "logs"
        config_dir = project_root / "storage" / "config"

    database_url = os.getenv("DATABASE_URL", default_db_url)
    audio_storage_dir = Path(os.getenv("AUDIO_STORAGE_DIR", str(default_audio)))

    return DataPaths(
        project_root=project_root,
        data_dir=data_dir,
        database_url=database_url,
        audio_storage_dir=audio_storage_dir,
        exports_dir=exports_dir,
        logs_dir=logs_dir,
        config_dir=config_dir,
    )


def ensure_data_dirs(paths: DataPaths) -> None:
    """Create the directory skeleton. Safe to call repeatedly; never migrates data."""

    paths.audio_storage_dir.mkdir(parents=True, exist_ok=True)
    paths.exports_dir.mkdir(parents=True, exist_ok=True)
    paths.logs_dir.mkdir(parents=True, exist_ok=True)
    paths.config_dir.mkdir(parents=True, exist_ok=True)
    # The SQLite parent dir (data root, or backend/) must exist before connect.
    if paths.database_url.startswith("sqlite:///"):
        db_file = Path(paths.database_url[len("sqlite:///") :])
        db_file.parent.mkdir(parents=True, exist_ok=True)
