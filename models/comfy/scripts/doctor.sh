#!/usr/bin/env bash
set -euo pipefail

# Project root (3 levels up from models/comfy/scripts/)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
# Default workspace is ComfyUI/ in project root
WORKSPACE="${COMFY_WORKSPACE:-$PROJECT_ROOT/ComfyUI}"
PORT="${COMFY_PORT:-8188}"

echo "== comfy doctor =="

if ! command -v comfy >/dev/null 2>&1; then
  echo "ERROR: comfy-cli not found (pipx install comfy-cli)."
  exit 1
fi

if [[ ! -d "$WORKSPACE" ]]; then
  echo "ERROR: $WORKSPACE not found. Run: task comfy:install"
  exit 1
fi

if command -v curl >/dev/null 2>&1; then
  if curl -fsS "http://localhost:$PORT" >/dev/null 2>&1; then
    echo "OK: ComfyUI reachable on http://localhost:$PORT"
  else
    echo "WARN: ComfyUI not reachable on http://localhost:$PORT (maybe not started)"
  fi
fi

echo "Workspace: $WORKSPACE"
echo "Done."
