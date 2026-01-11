$ErrorActionPreference = "Continue"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$Workspace = if ($env:COMFY_WORKSPACE) { $env:COMFY_WORKSPACE } else { $Root }
$Port = if ($env:COMFY_PORT) { $env:COMFY_PORT } else { "8188" }

Write-Host "== Stopping ComfyUI =="

# Try comfy stop first
& comfy --skip-prompt --no-enable-telemetry --workspace="$Workspace" stop 2>$null

# Fallback: kill process by port if comfy stop failed
$netstat = netstat -ano | Select-String ":$Port\s+.*LISTENING"
if ($netstat) {
    $pid = ($netstat -split '\s+')[-1]
    if ($pid -and $pid -ne "0") {
        Write-Host "Killing process on port $Port (PID: $pid)"
        Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
    }
}

Write-Host "ComfyUI stopped."
