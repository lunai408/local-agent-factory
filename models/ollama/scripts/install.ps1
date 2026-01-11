$ErrorActionPreference = "Stop"

Write-Host "== Installing Ollama on Windows =="

# winget (recommandé)
if (Get-Command winget -ErrorAction SilentlyContinue) {
  winget install --id Ollama.Ollama -e
  Write-Host "Done."
  exit 0
}

Write-Host "winget not found. Please install Ollama manually, then re-run doctor."
exit 1
