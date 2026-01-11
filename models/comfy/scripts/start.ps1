$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$Workspace = if ($env:COMFY_WORKSPACE) { $env:COMFY_WORKSPACE } else { $Root }

$Listen = if ($env:COMFY_LISTEN) { $env:COMFY_LISTEN } else { "0.0.0.0" }
$Port   = if ($env:COMFY_PORT) { $env:COMFY_PORT } else { "8188" }
$Vram   = if ($env:COMFY_VRAM_MODE) { $env:COMFY_VRAM_MODE } else { "auto" }

$extra = @()
switch ($Vram) {
  "lowvram" { $extra += "--lowvram" }
  "normalvram" { $extra += "--normalvram" }
  "highvram" { $extra += "--highvram" }
  "novram" { $extra += "--novram" }
  "cpu" { $extra += "--cpu" }
}

& comfy --skip-prompt --no-enable-telemetry --workspace="$Workspace" launch --background -- --listen $Listen --port $Port @extra
Write-Host "ComfyUI UI:  http://localhost:$Port"
