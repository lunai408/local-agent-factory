#!/usr/bin/env bash
set -euo pipefail

# Project root (3 levels up from models/comfy/scripts/)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
# Default workspace is ComfyUI/ in project root
WORKSPACE="${COMFY_WORKSPACE:-$PROJECT_ROOT/ComfyUI}"

echo "== ComfyUI uninstall =="

# stop if running
"$(dirname "$0")/stop.sh" || true

# remove workspace install
if [[ -d "$WORKSPACE" ]]; then
  rm -rf "$WORKSPACE"
  echo "Removed: $WORKSPACE"
fi

# optional: remove comfy-cli itself
if command -v pipx >/dev/null 2>&1; then
  pipx uninstall comfy-cli || true
  echo "Removed: comfy-cli (pipx)"
fi

echo "Done."
