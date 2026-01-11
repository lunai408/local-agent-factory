$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$Workspace = if ($env:COMFY_WORKSPACE) { $env:COMFY_WORKSPACE } else { $Root }

$Preset = if ($env:COMFY_PRESET) { $env:COMFY_PRESET } else { "z_image_turbo" }
if ($Preset -ne "z_image_turbo") {
    Write-Host "== ComfyUI pull models: preset '$Preset' (no-op) =="
    exit 0
}

Write-Host "== Pulling Z-Image Turbo models =="

# Optional token for gated HF downloads
if ($env:HF_API_TOKEN) {
    $env:HF_TOKEN = $env:HF_API_TOKEN
}

$TextUrl = if ($env:COMFY_ZIMAGE_TEXT_ENCODER_URL) { $env:COMFY_ZIMAGE_TEXT_ENCODER_URL } else { "https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/split_files/text_encoders/qwen_3_4b.safetensors?download=true" }
$DiffUrl = if ($env:COMFY_ZIMAGE_DIFFUSION_URL) { $env:COMFY_ZIMAGE_DIFFUSION_URL } else { "https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/split_files/diffusion_models/z_image_turbo_bf16.safetensors?download=true" }
$VaeUrl  = if ($env:COMFY_ZIMAGE_VAE_URL) { $env:COMFY_ZIMAGE_VAE_URL } else { "https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/split_files/vae/ae.safetensors?download=true" }

& comfy --skip-prompt --no-enable-telemetry --workspace="$Workspace" model download --url $TextUrl --relative-path "models/text_encoders"
& comfy --skip-prompt --no-enable-telemetry --workspace="$Workspace" model download --url $DiffUrl --relative-path "models/diffusion_models"
& comfy --skip-prompt --no-enable-telemetry --workspace="$Workspace" model download --url $VaeUrl  --relative-path "models/vae"

# Optional: Download LoRA if URL is defined
if ($env:COMFY_LORA_URL) {
    Write-Host "Downloading optional LoRA..."
    & comfy --skip-prompt --no-enable-telemetry --workspace="$Workspace" model download --url $env:COMFY_LORA_URL --relative-path "models/loras"
}

Write-Host "Done."
