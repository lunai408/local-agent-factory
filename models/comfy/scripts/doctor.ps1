$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$Workspace = if ($env:COMFY_WORKSPACE) { $env:COMFY_WORKSPACE } else { $Root }
$Port = if ($env:COMFY_PORT) { $env:COMFY_PORT } else { "8188" }

if (-not (Get-Command comfy -ErrorAction SilentlyContinue)) {
  Write-Host "ERROR: comfy not found."
  exit 1
}

if (-not (Test-Path (Join-Path $Workspace "ComfyUI"))) {
  Write-Host "ERROR: ComfyUI not installed in $Workspace\ComfyUI"
  exit 1
}

try {
  Invoke-WebRequest -UseBasicParsing "http://localhost:$Port" | Out-Null
  Write-Host "OK: http://localhost:$Port reachable"
} catch {
  Write-Host "WARN: not reachable (maybe not started)"
}
