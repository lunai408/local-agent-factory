#!/usr/bin/env bash
set -euo pipefail

# Project root (3 levels up from models/comfy/scripts/)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
# Default workspace is ComfyUI/ in project root
WORKSPACE="${COMFY_WORKSPACE:-$PROJECT_ROOT/ComfyUI}"

COMFY="comfy --skip-prompt --no-enable-telemetry --workspace=$WORKSPACE"

PRESET="${COMFY_PRESET:-z_image_turbo}"

if [[ "$PRESET" != "z_image_turbo" ]]; then
  echo "== ComfyUI pull models: preset '$PRESET' (no-op) =="
  exit 0
fi

echo "== Pulling Z-Image Turbo models =="

# Z Image Turbo files and locations are defined by ComfyUI examples.
TEXT_ENCODER_URL="${COMFY_ZIMAGE_TEXT_ENCODER_URL:-https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/split_files/text_encoders/qwen_3_4b.safetensors?download=true}"
DIFFUSION_URL="${COMFY_ZIMAGE_DIFFUSION_URL:-https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/split_files/diffusion_models/z_image_turbo_bf16.safetensors?download=true}"
VAE_URL="${COMFY_ZIMAGE_VAE_URL:-https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/split_files/vae/ae.safetensors?download=true}"

# Optional token for gated HF downloads
if [[ -n "${HF_API_TOKEN:-}" ]]; then
  export HF_API_TOKEN
fi

# Download into ComfyUI/models/ (standard ComfyUI structure)
$COMFY model download --url "$TEXT_ENCODER_URL" --relative-path "models/text_encoders"
$COMFY model download --url "$DIFFUSION_URL"     --relative-path "models/diffusion_models"
$COMFY model download --url "$VAE_URL"           --relative-path "models/vae"

# Optional: Download LoRA if URL is defined
if [[ -n "${COMFY_LORA_URL:-}" ]]; then
  echo "Downloading optional LoRA..."
  $COMFY model download --url "$COMFY_LORA_URL" --relative-path "models/loras"
fi

echo "Done."
