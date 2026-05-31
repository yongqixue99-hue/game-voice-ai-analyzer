#!/usr/bin/env bash
# Local ASR provider smoke check. It uses a throwaway LUNARIS_DATA_DIR and
# never touches the dev SQLite DB/audio directory.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
VENV_PY="$BACKEND_DIR/.venv/bin/python"
BACKEND_PORT="${LUNARIS_ASR_SMOKE_BACKEND_PORT:-18110}"
FAKE_FUNASR_PORT="${LUNARIS_ASR_SMOKE_FAKE_FUNASR_PORT:-18111}"
TMP_ROOT="$(mktemp -d -t lunaris-asr-smoke-XXXXXX)"

C_RESET=$'\033[0m'
C_OK=$'\033[32m'
C_INFO=$'\033[36m'

BACKEND_PID=""
FAKE_PID=""

cleanup() {
  [ -n "$BACKEND_PID" ] && kill "$BACKEND_PID" 2>/dev/null || true
  [ -n "$FAKE_PID" ] && kill "$FAKE_PID" 2>/dev/null || true
  rm -rf "$TMP_ROOT" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

ok() { printf "%s[PASS]%s %s\n" "$C_OK" "$C_RESET" "$*"; }
info() { printf "%s[INFO]%s %s\n" "$C_INFO" "$C_RESET" "$*"; }

require_tools() {
  [ -x "$VENV_PY" ] || { echo "缺少 backend/.venv/bin/python"; exit 1; }
  command -v curl >/dev/null 2>&1 || { echo "缺少 curl"; exit 1; }
}

make_wav() {
  local path="$1"
  "$VENV_PY" - "$path" <<'PY'
import struct
import sys
import wave

with wave.open(sys.argv[1], "w") as wav:
    wav.setnchannels(1)
    wav.setsampwidth(2)
    wav.setframerate(8000)
    wav.writeframes(b"".join(struct.pack("<h", 0) for _ in range(1600)))
PY
}

wait_http() {
  local url="$1"
  local attempts="${2:-40}"
  for _ in $(seq 1 "$attempts"); do
    if curl -fsS -m 2 "$url" >/dev/null 2>&1; then
      return 0
    fi
    sleep 0.25
  done
  return 1
}

stop_backend() {
  if [ -n "$BACKEND_PID" ]; then
    kill "$BACKEND_PID" 2>/dev/null || true
    wait "$BACKEND_PID" 2>/dev/null || true
    BACKEND_PID=""
  fi
}

start_backend() {
  local data_dir="$1"
  shift
  stop_backend
  mkdir -p "$data_dir"
  pushd "$BACKEND_DIR" >/dev/null
  env \
    LUNARIS_DATA_DIR="$data_dir" \
    LUNARIS_HOST=127.0.0.1 \
    LUNARIS_PORT="$BACKEND_PORT" \
    "$@" \
    "$VENV_PY" -m uvicorn app.main:app --host 127.0.0.1 --port "$BACKEND_PORT" \
      > "$data_dir/backend.log" 2>&1 &
  BACKEND_PID=$!
  popd >/dev/null
  wait_http "http://127.0.0.1:$BACKEND_PORT/api/health" 80 || {
    echo "后端启动失败，日志："
    tail -20 "$data_dir/backend.log" || true
    exit 1
  }
}

upload_wav() {
  local wav_path="$1"
  local response
  response="$(curl -fsS -m 10 -F "file=@$wav_path;type=audio/wav" "http://127.0.0.1:$BACKEND_PORT/api/recordings")"
  printf '%s' "$response" | "$VENV_PY" -c 'import json,sys; print(json.load(sys.stdin)["id"])'
}

transcribe_with_code() {
  local recording_id="$1"
  curl -sS -m 30 -w '\n%{http_code}' -X POST \
    "http://127.0.0.1:$BACKEND_PORT/api/recordings/$recording_id/transcribe"
}

analyze_with_code() {
  local recording_id="$1"
  curl -sS -m 30 -w '\n%{http_code}' -X POST \
    "http://127.0.0.1:$BACKEND_PORT/api/recordings/$recording_id/analyze"
}

assert_body_and_code() {
  local output="$1"
  local expected_code="$2"
  local expected_text="$3"
  local code body
  code="$(printf '%s' "$output" | tail -n 1)"
  body="$(printf '%s' "$output" | sed '$d')"
  [ "$code" = "$expected_code" ] || {
    echo "期望 HTTP $expected_code，实际 $code"
    echo "$body"
    exit 1
  }
  printf '%s' "$body" | grep -q "$expected_text" || {
    echo "响应中未找到：$expected_text"
    echo "$body"
    exit 1
  }
}

require_tools
make_wav "$TMP_ROOT/tiny.wav"

info "1. ASR_PROVIDER=mock"
start_backend "$TMP_ROOT/mock-data" ASR_PROVIDER=mock LLM_PROVIDER=mock
rid="$(upload_wav "$TMP_ROOT/tiny.wav")"
assert_body_and_code "$(transcribe_with_code "$rid")" "201" '"source":"mock"'
ok "mock transcribe 可用"

info "2. ASR_PROVIDER=funasr_http，服务不可达"
start_backend "$TMP_ROOT/funasr-down-data" \
  ASR_PROVIDER=funasr_http \
  FUNASR_HTTP_BASE_URL="http://127.0.0.1:$FAKE_FUNASR_PORT" \
  FUNASR_HTTP_TRANSCRIBE_PATH=/recognize \
  LLM_PROVIDER=mock
rid="$(upload_wav "$TMP_ROOT/tiny.wav")"
assert_body_and_code "$(transcribe_with_code "$rid")" "503" "FunASR 服务未连接"
ok "funasr_http 不可达时返回清晰错误"

info "3. 启动 fake FunASR server 后验证 funasr_http"
FAKE_FUNASR_QUIET=1 "$ROOT_DIR/scripts/fake_funasr_server.py" \
  --host 127.0.0.1 \
  --port "$FAKE_FUNASR_PORT" \
  > "$TMP_ROOT/fake-funasr.log" 2>&1 &
FAKE_PID=$!
wait_http "http://127.0.0.1:$FAKE_FUNASR_PORT/health" 40 || {
  echo "Fake FunASR 启动失败"
  tail -20 "$TMP_ROOT/fake-funasr.log" || true
  exit 1
}
start_backend "$TMP_ROOT/funasr-up-data" \
  ASR_PROVIDER=funasr_http \
  FUNASR_HTTP_BASE_URL="http://127.0.0.1:$FAKE_FUNASR_PORT" \
  FUNASR_HTTP_TRANSCRIBE_PATH=/recognize \
  LLM_PROVIDER=mock
rid="$(upload_wav "$TMP_ROOT/tiny.wav")"
assert_body_and_code "$(transcribe_with_code "$rid")" "201" '"source":"funasr_http"'
assert_body_and_code "$(analyze_with_code "$rid")" "201" '"provider":"mock"'
ok "fake FunASR -> transcript_segments -> mock AI summary 可用"

info "4. ASR_PROVIDER=aliyun 的本地 PUBLIC_BASE_URL 限制"
start_backend "$TMP_ROOT/aliyun-data" \
  ASR_PROVIDER=aliyun \
  DASHSCOPE_API_KEY=sk-smoke-dummy \
  PUBLIC_BASE_URL="http://127.0.0.1:$BACKEND_PORT" \
  LLM_PROVIDER=mock
rid="$(upload_wav "$TMP_ROOT/tiny.wav")"
assert_body_and_code "$(transcribe_with_code "$rid")" "400" "阿里云 ASR 无法访问本地音频"
ok "aliyun 本地 URL 错误清晰"

echo
ok "ASR provider smoke check 全部通过"
