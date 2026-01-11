$ErrorActionPreference = "Stop"

Write-Host "== ComfyUI install (Windows) =="

$Root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$Workspace = if ($env:COMFY_WORKSPACE) { $env:COMFY_WORKSPACE } else { $Root }

function Have($cmd) { Get-Command $cmd -ErrorAction SilentlyContinue | Out-Null; return $LASTEXITCODE -eq 0 }

if (-not (Have "pipx")) {
  Write-Host "pipx not found. Install it first (recommended) then re-run."
  Write-Host "Example: python -m pip install --user pipx ; python -m pipx ensurepath"
  exit 1
}

$env:PATH = "$env:USERPROFILE\.local\bin;$env:PATH"

pipx install -f comfy-cli 2>$null | Out-Null
pipx upgrade comfy-cli 2>$null | Out-Null

$Comfy = "comfy --skip-prompt --no-enable-telemetry"

& $Comfy tracking disable 2>$null | Out-Null

$accel = if ($env:COMFY_ACCELERATOR) { $env:COMFY_ACCELERATOR } else { "cpu" }
$flags = @()
if ($accel -eq "nvidia") { $flags += "--nvidia" } else { $flags += "--cpu" }

Write-Host "Installing ComfyUI into workspace: $Workspace"
& comfy --skip-prompt --no-enable-telemetry --workspace="$Workspace" install @flags
