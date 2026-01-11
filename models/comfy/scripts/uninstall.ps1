$ErrorActionPreference = "Continue"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$Workspace = if ($env:COMFY_WORKSPACE) { $env:COMFY_WORKSPACE } else { $Root }

& "$PSScriptRoot\stop.ps1"

$ComfyPath = Join-Path $Workspace "ComfyUI"
if (Test-Path $ComfyPath) {
  Remove-Item -Recurse -Force $ComfyPath
  Write-Host "Removed: $ComfyPath"
}

if (Get-Command pipx -ErrorAction SilentlyContinue) {
  pipx uninstall comfy-cli
}
