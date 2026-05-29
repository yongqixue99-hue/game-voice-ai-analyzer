#!/usr/bin/env bash
#
# Build the real LUNARIS FastAPI backend into a single-file sidecar executable
# for the *current platform only* (P6 spike).
#
# Output:  backend/dist/lunaris-real-backend          (raw PyInstaller onefile)
#          backend/dist/lunaris-real-backend-<triple>  (Tauri externalBin name)
#
# Both backend/dist and backend/build are gitignored; the .spec is committed.
#
# Usage:   cd backend && ./build-desktop-backend.sh
#
set -euo pipefail

BACKEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BACKEND_DIR"

VENV_PY="$BACKEND_DIR/.venv/bin/python"
if [[ ! -x "$VENV_PY" ]]; then
  echo "error: backend venv not found at $VENV_PY" >&2
  echo "       create it and 'pip install -e .' (plus pyinstaller) first." >&2
  exit 1
fi

if ! "$VENV_PY" -m PyInstaller --version >/dev/null 2>&1; then
  echo "error: PyInstaller not installed in backend venv." >&2
  echo "       run: $VENV_PY -m pip install pyinstaller==6.11.1" >&2
  exit 1
fi

echo ">> cleaning previous build artifacts"
rm -rf "$BACKEND_DIR/build" "$BACKEND_DIR/dist"

echo ">> running PyInstaller (lunaris-real-backend.spec)"
"$VENV_PY" -m PyInstaller --noconfirm --clean lunaris-real-backend.spec

RAW_BIN="$BACKEND_DIR/dist/lunaris-real-backend"
if [[ ! -f "$RAW_BIN" ]]; then
  echo "error: expected binary not produced: $RAW_BIN" >&2
  exit 1
fi

# Rust target triple for the Tauri externalBin naming convention.
TRIPLE="$("$BACKEND_DIR/.venv/bin/python" - <<'PY'
import platform
m = platform.machine().lower()
arch = {"x86_64": "x86_64", "amd64": "x86_64", "arm64": "aarch64", "aarch64": "aarch64"}.get(m, m)
sysname = platform.system().lower()
if sysname == "darwin":
    print(f"{arch}-apple-darwin")
elif sysname == "linux":
    print(f"{arch}-unknown-linux-gnu")
elif sysname == "windows":
    print(f"{arch}-pc-windows-msvc")
else:
    print(f"{arch}-{sysname}")
PY
)"

cp "$RAW_BIN" "$BACKEND_DIR/dist/lunaris-real-backend-$TRIPLE"

echo ">> done"
echo "   raw:    $RAW_BIN"
echo "   triple: $BACKEND_DIR/dist/lunaris-real-backend-$TRIPLE"
echo
echo "Smoke test:"
echo "  LUNARIS_DATA_DIR=/tmp/lunaris-real LUNARIS_PORT=18080 \"$RAW_BIN\" &"
echo "  curl http://127.0.0.1:18080/api/health"
