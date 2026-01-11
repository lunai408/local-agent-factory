#!/usr/bin/env bash
set -euo pipefail

# Project root (3 levels up from models/comfy/scripts/)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
# Default workspace is ComfyUI/ in project root
WORKSPACE="${COMFY_WORKSPACE:-$PROJECT_ROOT/ComfyUI}"

LISTEN="${COMFY_LISTEN:-0.0.0.0}"
PORT="${COMFY_PORT:-8188}"
VRAM="${COMFY_VRAM_MODE:-auto}"

EXTRA=()
case "$VRAM" in
  auto) ;;
  lowvram) EXTRA+=(--lowvram) ;;
  normalvram) EXTRA+=(--normalvram) ;;
  highvram) EXTRA+=(--highvram) ;;
  novram) EXTRA+=(--novram) ;;
  cpu) EXTRA+=(--cpu) ;;
  *) echo "Unknown COMFY_VRAM_MODE=$VRAM"; exit 1 ;;
esac

COMFY="comfy --skip-prompt --no-enable-telemetry --workspace=$WORKSPACE"

echo "== starting ComfyUI =="

# Build command
CMD="$COMFY launch -- --listen $LISTEN --port $PORT"
if [[ ${#EXTRA[@]} -gt 0 ]]; then
  CMD="$CMD ${EXTRA[*]}"
fi

# Run in background using nohup (comfy --background has asyncio issues on Python 3.14)
nohup $CMD > /tmp/comfy.log 2>&1 &
disown

echo "ComfyUI starting in background... Logs: /tmp/comfy.log"
sleep 2

echo "ComfyUI UI:  http://localhost:$PORT"
echo "ComfyUI API: http://localhost:$PORT"
