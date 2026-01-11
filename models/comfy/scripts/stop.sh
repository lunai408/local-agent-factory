#!/usr/bin/env bash
set -euo pipefail

# Project root (3 levels up from models/comfy/scripts/)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
# Default workspace is ComfyUI/ in project root
WORKSPACE="${COMFY_WORKSPACE:-$PROJECT_ROOT/ComfyUI}"
COMFY="comfy --skip-prompt --no-enable-telemetry --workspace=$WORKSPACE"

echo "== stopping ComfyUI =="
$COMFY stop || true

# Fallback: kill by port (best-effort)
PORT="${COMFY_PORT:-8188}"
if command -v lsof >/dev/null 2>&1; then
  PIDS="$(lsof -ti tcp:"$PORT" 2>/dev/null || true)"
  for PID in $PIDS; do
    kill "$PID" 2>/dev/null || true
  done
fi

echo "Stopped."
