"""Desktop sidecar entry point for the real FastAPI backend.

Run from source::

    python backend/desktop_entry.py

Or as a PyInstaller-frozen executable (see ``build-desktop-backend.sh``).

Environment:
  LUNARIS_DATA_DIR  Data root. When set, db/audio/exports/logs/config live here
                    (see app.paths). When unset, the source-tree dev layout is
                    used unchanged.
  LUNARIS_HOST      Bind host. Default 127.0.0.1.
  LUNARIS_PORT      Bind port. Default 18080 (avoids the dev backend on 8000).

Health check once running: GET http://127.0.0.1:18080/api/health -> {"status":"ok"}.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path


def _ensure_backend_on_path() -> None:
    """Make ``app`` importable whether running from source or frozen.

    From source this file lives in ``backend/``; its own dir holds the ``app``
    package. Under PyInstaller the modules are already on ``sys.path`` via the
    bundled archive, so adding the (temp) dir is harmless.
    """

    backend_dir = Path(__file__).resolve().parent
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))


def _configure_logging() -> logging.Logger:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    return logging.getLogger("lunaris.desktop_entry")


def main() -> None:
    log = _configure_logging()
    _ensure_backend_on_path()

    host = os.environ.get("LUNARIS_HOST", "127.0.0.1")
    port = int(os.environ.get("LUNARIS_PORT", "18080"))
    frozen = bool(getattr(sys, "frozen", False))

    # Resolve + create the data directory skeleton before the app imports the DB.
    from app.config import get_settings
    from app.paths import ensure_data_dirs, resolve_data_paths

    settings = get_settings()
    paths = resolve_data_paths(settings.project_root)
    ensure_data_dirs(paths)

    log.info("LUNARIS real backend starting (frozen=%s)", frozen)
    log.info("data_dir=%s", paths.data_dir or "<dev source tree>")
    log.info("database_url=%s", settings.database_url)
    log.info("audio_storage_dir=%s", settings.audio_storage_dir)
    log.info("binding http://%s:%s (health: /api/health)", host, port)

    import uvicorn

    from app.main import app

    # loop="asyncio" avoids PyInstaller pulling uvloop; the FastAPI lifespan
    # creates the DB schema + audio dir on startup.
    uvicorn.run(app, host=host, port=port, log_level="info", loop="asyncio")


if __name__ == "__main__":
    main()
