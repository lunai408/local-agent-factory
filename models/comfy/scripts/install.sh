#!/usr/bin/env bash
set -euo pipefail

echo "== ComfyUI install (PEP668-safe via pipx) =="

# Project root (3 levels up from models/comfy/scripts/)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
# Default workspace is ComfyUI/ in project root
WORKSPACE="${COMFY_WORKSPACE:-$PROJECT_ROOT/ComfyUI}"

need() { command -v "$1" >/dev/null 2>&1; }

if ! need pipx; then
  echo "pipx not found. Installing..."
  if need brew; then
    brew install pipx
  elif need apt-get; then
    sudo apt-get update
    sudo apt-get install -y pipx
    pipx ensurepath
  else
    echo "ERROR: install pipx manually (brew/apt) then re-run."
    exit 1
  fi
fi

# Ensure pipx bin is in PATH for current session
export PATH="$HOME/.local/bin:$PATH"

echo "Installing/updating comfy-cli with pipx..."
pipx install -f comfy-cli >/dev/null 2>&1 || pipx upgrade comfy-cli

# Make comfy-cli non-interactive (skip prompt + disable telemetry prompt)
# --skip-prompt / --no-enable-telemetry are used in comfy-cli scripting contexts. 
COMFY="comfy --skip-prompt --no-enable-telemetry"

# Disable tracking prompt if it ever appears. 
$COMFY tracking disable >/dev/null 2>&1 || true

ACCEL="${COMFY_ACCELERATOR:-auto}"
INSTALL_FLAGS=()

case "$ACCEL" in
  auto)
    # Auto-detection:
    # - macOS: --cpu pour l'installation, PyTorch utilisera MPS au runtime sur Apple Silicon
    # - linux: nvidia si nvidia-smi existe, sinon cpu
    if [[ "$(uname -s)" == "Darwin" ]]; then
      echo "macOS detected: installing with --cpu (PyTorch will use MPS at runtime)"
      INSTALL_FLAGS+=(--cpu)
    else
      if command -v nvidia-smi >/dev/null 2>&1; then
        INSTALL_FLAGS+=(--nvidia)
      else
        INSTALL_FLAGS+=(--cpu)
      fi
    fi
    ;;
  cpu) INSTALL_FLAGS+=(--cpu) ;;
  nvidia) INSTALL_FLAGS+=(--nvidia) ;;
  amd)
    # comfy-cli flags for AMD can vary by version; try common ones.
    INSTALL_FLAGS+=(--amd)
    ;;
  *)
    echo "ERROR: COMFY_ACCELERATOR must be auto|cpu|nvidia|amd (got: $ACCEL)"
    exit 1
    ;;
esac

echo "Installing ComfyUI into workspace: $WORKSPACE"
set +e
if [[ ${#INSTALL_FLAGS[@]} -gt 0 ]]; then
  $COMFY --workspace="$WORKSPACE" install "${INSTALL_FLAGS[@]}"
else
  $COMFY --workspace="$WORKSPACE" install
fi
RC=$?
set -e

if [[ $RC -ne 0 && "$ACCEL" == "amd" ]]; then
  echo "AMD install flag failed; retrying with --rocm..."
  $COMFY --workspace="$WORKSPACE" install --rocm
fi

echo "ComfyUI installed."
