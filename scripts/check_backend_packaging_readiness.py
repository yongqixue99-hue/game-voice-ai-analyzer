#!/usr/bin/env python3
"""Read-only readiness audit for packaging the real backend as a Tauri sidecar.

P3 (real-backend-sidecar-readiness) helper. This script ONLY inspects:
  - whether we are running frozen (PyInstaller) or from source,
  - the resolved data paths (project_root / DB / audio) the backend would use,
  - third-party imports actually used by backend/app,
  - `__file__`-based path assumptions that break when frozen,
  - PyInstaller hidden-import candidates.

It MUST NOT have side effects: it does not create the DB, write files, mkdir,
or make any ASR/LLM network call. API keys are reported as present/absent only
(never printed). Run with the backend venv:

    backend/.venv/bin/python scripts/check_backend_packaging_readiness.py
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "backend"
APP_DIR = BACKEND_DIR / "app"

STDLIB_HINTS = {
    "__future__", "ast", "collections", "contextlib", "dataclasses", "datetime",
    "json", "logging", "mimetypes", "os", "pathlib", "re", "sys", "time",
    "typing", "urllib", "uuid", "email", "sqlite3",
}
SDK_FLAGS = {"requests", "httpx", "openai", "dashscope", "aiohttp"}
HIDDEN_IMPORT_CANDIDATES = [
    "sqlalchemy.dialects.sqlite",
    "uvicorn.lifespan.on",
    "uvicorn.lifespan.off",
    "uvicorn.protocols.http.h11_impl",
    "uvicorn.loops.asyncio",
]


def hr(title: str) -> None:
    print(f"\n=== {title} ===")


def detect_frozen() -> None:
    hr("Runtime")
    frozen = getattr(sys, "frozen", False)
    meipass = getattr(sys, "_MEIPASS", None)
    print(f"frozen (PyInstaller): {bool(frozen)}")
    print(f"_MEIPASS: {meipass}")
    print(f"python: {sys.version.split()[0]}")


def scan_imports() -> None:
    hr("Third-party imports used by backend/app (static scan)")
    top_level: dict[str, set[str]] = {}
    file_uses: list[str] = []
    for py in sorted(APP_DIR.glob("*.py")):
        try:
            tree = ast.parse(py.read_text(encoding="utf-8"))
        except (OSError, SyntaxError) as exc:  # pragma: no cover - defensive
            print(f"  ! could not parse {py.name}: {exc}")
            continue
        if "__file__" in py.read_text(encoding="utf-8"):
            file_uses.append(py.name)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top_level.setdefault(alias.name.split(".")[0], set()).add(py.name)
            elif isinstance(node, ast.ImportFrom):
                if node.level and node.level > 0:
                    continue  # relative (local app) import
                if node.module:
                    top_level.setdefault(node.module.split(".")[0], set()).add(py.name)

    third_party = {
        mod: files
        for mod, files in top_level.items()
        if mod not in STDLIB_HINTS and mod != "app"
    }
    for mod in sorted(third_party):
        print(f"  {mod:<16} <- {', '.join(sorted(third_party[mod]))}")

    flagged = sorted(set(third_party) & SDK_FLAGS)
    print("\nHeavy ASR/LLM SDKs in use:", flagged or "NONE (urllib-only HTTP) ✓")

    hr("`__file__` path assumptions (break when frozen)")
    print("files referencing __file__:", ", ".join(file_uses) or "none")
    print("note: config.py uses Path(__file__).resolve().parents[2] as project_root")


def resolved_paths() -> None:
    hr("Resolved settings paths (no side effects)")
    sys.path.insert(0, str(BACKEND_DIR))
    try:
        from app.config import get_settings  # type: ignore
    except Exception as exc:  # pragma: no cover - defensive
        print(f"  ! could not import app.config: {exc}")
        return
    s = get_settings()
    print(f"project_root:       {s.project_root}")
    print(f"database_url:       {s.database_url}")
    print(f"audio_storage_dir:  {s.audio_storage_dir}")
    print(f"asr_provider:       {s.asr_provider}")
    print(f"public_base_url:    {s.public_base_url}")
    print(f"llm_provider:       {s.llm_provider}")
    # secrets: presence only, never the value
    print(f"DASHSCOPE_API_KEY set: {bool(s.dashscope_api_key)}")
    print(f"OPENAI_API_KEY set:    {bool(s.openai_api_key)}")

    hr("Frozen-safety check")
    inside_repo = str(s.audio_storage_dir).startswith(str(REPO_ROOT)) or str(
        s.database_url
    ).find(str(REPO_ROOT)) != -1
    if inside_repo:
        print("⚠ DB/audio resolve INSIDE the repo tree (source-relative).")
        print("  Under PyInstaller these would land in the temp extraction dir.")
        print("  → P4 must inject LUNARIS_DATA_DIR and resolve paths from it.")
    else:
        print("DB/audio resolve outside repo (data-dir injection appears active).")


def hidden_import_checklist() -> None:
    hr("PyInstaller hidden-import candidates (verify in P6 spike)")
    for name in HIDDEN_IMPORT_CANDIDATES:
        print(f"  - {name}")
    print("  also: --collect-submodules app, --collect-all pydantic (pydantic_core)")


def main() -> None:
    print("LUNARIS real-backend sidecar packaging readiness (READ-ONLY)")
    detect_frozen()
    scan_imports()
    resolved_paths()
    hidden_import_checklist()
    print("\nDone. No files, DB, or network were modified.")


if __name__ == "__main__":
    main()
