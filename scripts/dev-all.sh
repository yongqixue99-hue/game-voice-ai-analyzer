#!/usr/bin/env bash
# LUNARIS dev-all: one-shot launcher for backend + frontend + tauri dev.
# Ctrl+C cleans up all three children. Manual three-terminal flow remains usable.

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
VENV_DIR="$BACKEND_DIR/.venv"

C_RESET=$'\033[0m'
C_BACK=$'\033[36m'    # cyan
C_FRONT=$'\033[35m'   # magenta
C_TAURI=$'\033[33m'   # yellow
C_ERR=$'\033[31m'
C_OK=$'\033[32m'

log()   { printf "%s[dev-all]%s %s\n" "$C_OK" "$C_RESET" "$*"; }
warn()  { printf "%s[dev-all]%s %s\n" "$C_ERR" "$C_RESET" "$*" >&2; }
die()   { warn "$*"; exit 1; }

# --- preflight ---------------------------------------------------------------

[ -d "$VENV_DIR" ]                  || die "缺少 backend/.venv，请先创建虚拟环境并安装依赖"
[ -x "$VENV_DIR/bin/uvicorn" ]      || die "backend/.venv 内未找到 uvicorn，请先安装后端依赖"
[ -d "$FRONTEND_DIR/node_modules" ] || die "缺少 frontend/node_modules，请先在 frontend/ 执行 npm install"
command -v cargo >/dev/null 2>&1    || die "未找到 cargo/rustc，请先安装 Rust 工具链"

port_busy() { lsof -i ":$1" -P -n 2>/dev/null | grep -q LISTEN; }
port_busy 8000 && die "端口 8000 已被占用，请先停止占用进程（lsof -i:8000）"
port_busy 3000 && die "端口 3000 已被占用，请先停止占用进程（lsof -i:3000）"

# --- child management --------------------------------------------------------

PIDS=()
CLEANING=0

kill_descendants() {
  local parent="$1" sig="$2"
  local kids
  kids=$(pgrep -P "$parent" 2>/dev/null || true)
  for k in $kids; do
    kill_descendants "$k" "$sig"
    kill "-$sig" "$k" 2>/dev/null || true
  done
}

cleanup() {
  [ "$CLEANING" -eq 1 ] && return
  CLEANING=1
  echo
  log "正在清理子进程…"
  # 1. 按已记录的 pgid 优雅终止
  for pid in "${PIDS[@]}"; do
    [ -n "$pid" ] && kill -TERM "-$pid" 2>/dev/null || true
  done
  # 2. 兜底：递归终止本脚本的全部后代（覆盖管道、subshell、孙进程）
  kill_descendants $$ TERM
  sleep 1
  for pid in "${PIDS[@]}"; do
    [ -n "$pid" ] && kill -KILL "-$pid" 2>/dev/null || true
  done
  kill_descendants $$ KILL
  # 3. 模式兜底：Tauri dev 会派生独立的 cargo / lunaris-desktop
  pkill -f "target/debug/lunaris-desktop" 2>/dev/null || true
  log "完成"
}
trap cleanup EXIT INT TERM

prefix_stream() {
  local color="$1" label="$2"
  while IFS= read -r line; do
    printf "%s[%s]%s %s\n" "$color" "$label" "$C_RESET" "$line"
  done
}

spawn() {
  local color="$1" label="$2"; shift 2
  set -m
  ( "$@" 2>&1 | prefix_stream "$color" "$label" ) &
  local pid=$!
  set +m
  PIDS+=("$pid")
  log "已启动 [$label] (pgid=$pid)"
}

# --- launch ------------------------------------------------------------------

log "项目根目录：$ROOT_DIR"

spawn "$C_BACK" "backend" \
  bash -c "cd '$BACKEND_DIR' && source '$VENV_DIR/bin/activate' && exec uvicorn app.main:app --reload --port 8000"

spawn "$C_FRONT" "frontend" \
  bash -c "cd '$FRONTEND_DIR' && exec npm run dev"

spawn "$C_TAURI" "tauri" \
  bash -c "cd '$FRONTEND_DIR' && exec npm run tauri dev"

log "三个进程已启动，按 Ctrl+C 统一停止"

# 任一子进程退出即整体收尾
wait -n 2>/dev/null || wait
