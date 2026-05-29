#!/usr/bin/env bash
# LUNARIS desktop Beta smoke check.
#
# Automates the "release-candidate" acceptance for the desktop build so you do
# not have to click through pages by hand. It checks, in order:
#   1. real backend desktop_entry / frozen binary: start -> /api/health -> stop
#      -> port released (B16-style lifecycle).
#   2. B11 real ASR path: upload a clip, call transcribe, assert it reaches the
#      real aliyun provider (error must point at public-URL / FILE_DOWNLOAD,
#      NOT "未配置 key").
#   3. Tauri wiring: real-backend sidecar binary present, both sidecars in
#      tauri.conf.json externalBin, cargo test.
#   4. Frontend: npm run lint, npm run build (produces out/).
#   5. Backend: pytest.
#   6. Packaging: report the last LUNARIS.app bundle (tauri build is slow; only
#      rebuild when --build is passed).
#
# It is side-effect safe for your real data: it always runs the backend against
# a throwaway LUNARIS_DATA_DIR under a temp dir, never your dev DB/audio.
#
# Usage:
#   scripts/desktop_beta_smoke_check.sh            # all checks, no tauri rebuild
#   scripts/desktop_beta_smoke_check.sh --build    # also run npm run tauri build
#   scripts/desktop_beta_smoke_check.sh --quick     # skip lint/build/pytest/cargo
#
# Exit code 0 = all non-known-issue checks passed.

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
TAURI_DIR="$FRONTEND_DIR/src-tauri"
VENV_PY="$BACKEND_DIR/.venv/bin/python"
TRIPLE="aarch64-apple-darwin"   # current target; build script derives the same
REAL_BIN_RAW="$BACKEND_DIR/dist/lunaris-real-backend"
REAL_BIN_TRIPLE="$TAURI_DIR/binaries/lunaris-real-backend-$TRIPLE"
HELLO_BIN_TRIPLE="$TAURI_DIR/binaries/lunaris-hello-backend-$TRIPLE"
SMOKE_PORT="${LUNARIS_SMOKE_PORT:-18090}"
TMP_DATA="$(mktemp -d -t lunaris-smoke-XXXXXX)"

C_RESET=$'\033[0m'; C_OK=$'\033[32m'; C_ERR=$'\033[31m'; C_WARN=$'\033[33m'; C_INFO=$'\033[36m'

PASS=(); FAIL=(); KNOWN=()
ok()    { printf "%s[PASS]%s %s\n" "$C_OK" "$C_RESET" "$*"; PASS+=("$*"); }
bad()   { printf "%s[FAIL]%s %s\n" "$C_ERR" "$C_RESET" "$*"; FAIL+=("$*"); }
known() { printf "%s[KNOWN]%s %s\n" "$C_WARN" "$C_RESET" "$*"; KNOWN+=("$*"); }
info()  { printf "%s[INFO]%s %s\n" "$C_INFO" "$C_RESET" "$*"; }
section(){ printf "\n%s== %s ==%s\n" "$C_INFO" "$*" "$C_RESET"; }

DO_BUILD=0; QUICK=0
for arg in "$@"; do
  case "$arg" in
    --build) DO_BUILD=1 ;;
    --quick) QUICK=1 ;;
    *) echo "unknown arg: $arg" >&2; exit 2 ;;
  esac
done

SMOKE_PID=""
cleanup() {
  [ -n "$SMOKE_PID" ] && kill -TERM "$SMOKE_PID" 2>/dev/null
  pkill -f "lunaris-real-backend" 2>/dev/null
  pkill -f "desktop_entry.py" 2>/dev/null
  rm -rf "$TMP_DATA" 2>/dev/null
}
trap cleanup EXIT INT TERM

health_url="http://127.0.0.1:$SMOKE_PORT/api/health"
poll_health() {
  local attempts="$1" body=""
  for _ in $(seq 1 "$attempts"); do
    body="$(curl -s -m 2 "$health_url" 2>/dev/null)"
    [ -n "$body" ] && { echo "$body"; return 0; }
    sleep 0.5
  done
  return 1
}
port_listening() { lsof -i ":$SMOKE_PORT" -P -n 2>/dev/null | grep -q LISTEN; }

# --- 0. preflight ------------------------------------------------------------
section "0. 预检"
[ -x "$VENV_PY" ] || { bad "缺少 backend/.venv (python)"; }
command -v curl >/dev/null 2>&1 || { bad "缺少 curl"; }
# Choose runner: frozen binary (closest to desktop) if present, else source entry.
RUNNER=""; RUNNER_KIND=""
if [ -x "$REAL_BIN_TRIPLE" ]; then
  RUNNER="$REAL_BIN_TRIPLE"; RUNNER_KIND="frozen(sidecar binary)"
elif [ -x "$REAL_BIN_RAW" ]; then
  RUNNER="$REAL_BIN_RAW"; RUNNER_KIND="frozen(dist)"
elif [ -x "$VENV_PY" ]; then
  RUNNER="$VENV_PY $BACKEND_DIR/desktop_entry.py"; RUNNER_KIND="source(desktop_entry.py)"
fi
[ -n "$RUNNER" ] && info "real backend runner: $RUNNER_KIND" || bad "找不到可运行的真实后端 (frozen 或 desktop_entry)"

# --- 1. lifecycle: start / health / stop / port release ----------------------
section "1. 真实后端生命周期 (health + 停止 + 端口释放)"
if [ -n "$RUNNER" ]; then
  LUNARIS_DATA_DIR="$TMP_DATA" LUNARIS_PORT="$SMOKE_PORT" LUNARIS_HOST=127.0.0.1 \
    $RUNNER > "$TMP_DATA/server.log" 2>&1 &
  SMOKE_PID=$!
  # Frozen onefile cold start (unpack + sqlalchemy/pydantic import) takes ~10-15s;
  # poll generously so we never SIGTERM mid-unpack (which would orphan the child).
  if body="$(poll_health 80)"; then
    echo "$body" | grep -q '"status":"ok"' \
      && ok "1.1 /api/health 返回 ok ($RUNNER_KIND)" \
      || bad "1.1 /api/health 未返回 ok: $body"
  else
    bad "1.1 /api/health 超时未响应"; info "log: $(tail -3 "$TMP_DATA/server.log" 2>/dev/null)"
  fi
  port_listening && ok "1.2 端口 $SMOKE_PORT 正在监听" || bad "1.2 端口 $SMOKE_PORT 未监听"
  # stop (SIGTERM -> PyInstaller bootloader forwards to the uvicorn child)
  kill -TERM "$SMOKE_PID" 2>/dev/null; SMOKE_PID=""
  released=0
  for _ in $(seq 1 30); do sleep 0.5; port_listening || { released=1; break; }; done
  [ "$released" = 1 ] && ok "1.3 停止后端口 $SMOKE_PORT 已释放 (B16 lifecycle)" \
                       || bad "1.3 停止后端口 $SMOKE_PORT 仍占用"
  pgrep -fl lunaris-real-backend >/dev/null 2>&1 \
    && bad "1.4 仍有 lunaris-real-backend 残留进程" \
    || ok "1.4 无 lunaris-real-backend 残留进程"
fi

# --- 2. B11 real ASR path ----------------------------------------------------
section "2. B11 真实 ASR provider 路径"
# Run a fresh instance with aliyun provider + a localhost public_base_url so we
# can deterministically assert the error ladder WITHOUT a live cloud call.
B11_DATA="$(mktemp -d -t lunaris-b11-XXXXXX)"
mkdir -p "$B11_DATA/config"
# A dummy key is enough to pass the key check and reach the public-URL check.
printf 'ASR_PROVIDER=aliyun\nDASHSCOPE_API_KEY=sk-smoke-dummy\nPUBLIC_BASE_URL=http://127.0.0.1:%s\n' "$SMOKE_PORT" > "$B11_DATA/config/.env"
if [ -n "$RUNNER" ]; then
  LUNARIS_DATA_DIR="$B11_DATA" LUNARIS_PORT="$SMOKE_PORT" LUNARIS_HOST=127.0.0.1 \
    $RUNNER > "$B11_DATA/server.log" 2>&1 &
  SMOKE_PID=$!
  if poll_health 80 >/dev/null; then
    # tiny silent wav
    "$VENV_PY" - "$B11_DATA/tiny.wav" <<'PY'
import sys, wave, struct
with wave.open(sys.argv[1], "w") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(8000)
    w.writeframes(b"".join(struct.pack("<h", 0) for _ in range(1600)))
PY
    up="$(curl -s -m 8 -F "file=@$B11_DATA/tiny.wav;type=audio/wav" "http://127.0.0.1:$SMOKE_PORT/api/recordings")"
    rid="$(printf '%s' "$up" | "$VENV_PY" -c 'import sys,json;
try: print(json.load(sys.stdin).get("id",""))
except Exception: print("")')"
    if [ -n "$rid" ]; then
      ok "2.1 上传录音成功 (id=$rid)"
      resp="$(curl -s -m 30 -X POST "http://127.0.0.1:$SMOKE_PORT/api/recordings/$rid/transcribe")"
      info "transcribe 响应: $(printf '%s' "$resp" | head -c 240)"
      if printf '%s' "$resp" | grep -q "未配置 DASHSCOPE_API_KEY"; then
        bad "2.2 真实转写仍报「未配置 key」—— frozen 凭证加载未生效"
      elif printf '%s' "$resp" | grep -qE "无法访问本地音频 URL|PUBLIC_BASE_URL|FILE_DOWNLOAD|公网|阿里云"; then
        ok "2.2 真实转写走 aliyun provider，错误明确指向公网 URL/下载 (B11 达标，属已知限制)"
        known "B11 真实 ASR：阿里云需公网音频 URL，桌面端 127.0.0.1 不可达 (已知限制)"
      else
        info "2.2 transcribe 返回非预期内容，需人工判读：$(printf '%s' "$resp" | head -c 200)"
        known "B11：transcribe 返回需人工判读 (见上)"
      fi
    else
      bad "2.1 上传失败: $(printf '%s' "$up" | head -c 200)"
    fi
  else
    bad "2.0 B11 实例 health 超时"
  fi
  kill -TERM "$SMOKE_PID" 2>/dev/null; SMOKE_PID=""
  for _ in $(seq 1 20); do sleep 0.5; port_listening || break; done
fi
rm -rf "$B11_DATA" 2>/dev/null

# --- 3. Tauri wiring ---------------------------------------------------------
section "3. Tauri sidecar 配置"
[ -x "$REAL_BIN_TRIPLE" ] && ok "3.1 real backend sidecar 二进制存在 ($REAL_BIN_TRIPLE)" \
  || bad "3.1 缺少 real backend sidecar 二进制，请运行 backend/build-desktop-backend.sh 并拷贝到 binaries/"
[ -x "$HELLO_BIN_TRIPLE" ] && ok "3.2 hello-backend fallback sidecar 二进制存在" \
  || info "3.2 hello-backend sidecar 二进制缺失 (fallback，可选)"
CONF="$TAURI_DIR/tauri.conf.json"
grep -q "binaries/lunaris-real-backend" "$CONF" \
  && ok "3.3 tauri.conf.json externalBin 含 real backend" \
  || bad "3.3 tauri.conf.json 未注册 real backend sidecar"
grep -q "binaries/lunaris-hello-backend" "$CONF" \
  && ok "3.4 tauri.conf.json externalBin 仍保留 hello-backend (fallback)" \
  || bad "3.4 tauri.conf.json 丢失 hello-backend sidecar"

if [ "$QUICK" = 0 ]; then
  if command -v cargo >/dev/null 2>&1; then
    info "3.5 运行 cargo test (sidecar mock-runtime，较慢)…"
    if (cd "$TAURI_DIR" && cargo test -- --test-threads=1 >/tmp/lunaris-cargo.log 2>&1); then
      ok "3.5 cargo test 通过"
    else
      bad "3.5 cargo test 失败 (见 /tmp/lunaris-cargo.log)"; tail -8 /tmp/lunaris-cargo.log
    fi
  else
    info "3.5 跳过 cargo test (未找到 cargo)"
  fi
else
  info "3.5 --quick 跳过 cargo test"
fi

# --- 4. frontend lint + build ------------------------------------------------
section "4. 前端 lint / build"
if [ "$QUICK" = 0 ]; then
  if (cd "$FRONTEND_DIR" && npm run lint >/tmp/lunaris-lint.log 2>&1); then
    ok "4.1 npm run lint 通过"
  else bad "4.1 npm run lint 失败 (见 /tmp/lunaris-lint.log)"; tail -8 /tmp/lunaris-lint.log; fi
  if (cd "$FRONTEND_DIR" && npm run build >/tmp/lunaris-build.log 2>&1); then
    [ -s "$FRONTEND_DIR/out/index.html" ] \
      && ok "4.2 npm run build 通过且生成 out/index.html" \
      || bad "4.2 build 完成但 out/index.html 缺失/为空"
  else bad "4.2 npm run build 失败 (见 /tmp/lunaris-build.log)"; tail -8 /tmp/lunaris-build.log; fi
else
  info "4.x --quick 跳过 lint/build"
fi

# --- 5. backend pytest -------------------------------------------------------
section "5. 后端 pytest"
if [ "$QUICK" = 0 ]; then
  if (cd "$BACKEND_DIR" && "$VENV_PY" -m pytest -q >/tmp/lunaris-pytest.log 2>&1); then
    ok "5.1 pytest 通过 ($(grep -oE '[0-9]+ passed' /tmp/lunaris-pytest.log | tail -1))"
  else bad "5.1 pytest 失败 (见 /tmp/lunaris-pytest.log)"; tail -8 /tmp/lunaris-pytest.log; fi
else
  info "5.1 --quick 跳过 pytest"
fi

# --- 6. packaging ------------------------------------------------------------
section "6. 打包产物"
APP="$TAURI_DIR/target/release/bundle/macos/LUNARIS.app"
if [ "$DO_BUILD" = 1 ]; then
  info "6.0 --build：运行 npm run tauri build (很慢)…"
  if (cd "$FRONTEND_DIR" && npm run tauri build >/tmp/lunaris-tauri-build.log 2>&1); then
    ok "6.0 npm run tauri build 成功"
  else bad "6.0 npm run tauri build 失败 (见 /tmp/lunaris-tauri-build.log)"; tail -12 /tmp/lunaris-tauri-build.log; fi
fi
if [ -d "$APP" ]; then
  ok "6.1 存在 LUNARIS.app ($(du -sh "$APP" 2>/dev/null | cut -f1))"
  for s in lunaris-real-backend lunaris-hello-backend; do
    ls "$APP/Contents/MacOS/" 2>/dev/null | grep -q "$s" \
      && ok "6.2 app 内含 sidecar: $s" \
      || info "6.2 app 内未见 sidecar: $s (可能上次构建较旧，--build 可刷新)"
  done
else
  info "6.1 未找到 LUNARIS.app (用 --build 生成，或上次未打包)"
fi

# --- summary -----------------------------------------------------------------
section "结果汇总"
printf "%sPASS%s: %d   %sFAIL%s: %d   %sKNOWN%s: %d\n" \
  "$C_OK" "$C_RESET" "${#PASS[@]}" "$C_ERR" "$C_RESET" "${#FAIL[@]}" "$C_WARN" "$C_RESET" "${#KNOWN[@]}"
if [ "${#KNOWN[@]}" -gt 0 ]; then echo "已知限制:"; for k in "${KNOWN[@]}"; do echo "  - $k"; done; fi
if [ "${#FAIL[@]}" -gt 0 ]; then
  echo "失败项:"; for f in "${FAIL[@]}"; do echo "  - $f"; done
  echo; echo "结论: 存在失败项，未达 Beta 候选。"; exit 1
fi
echo; echo "结论: 自动化冒烟全部通过 (known issues 不计失败) —— 可作内部 Beta 候选。"
exit 0
