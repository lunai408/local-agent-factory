$ErrorActionPreference = "Stop"

Write-Host "== Uninstall Ollama (Windows) =="

# Stop process
Get-Process ollama -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

# Try winget uninstall
if (Get-Command winget -ErrorAction SilentlyContinue) {
  winget uninstall --id Ollama.Ollama -e
  Write-Host "Uninstalled via winget."
} else {
  Write-Host "winget not found. Please uninstall Ollama from Settings > Apps."
}

# Optional purge data
if ($env:OLLAMA_PURGE_DATA -eq "1") {
  $path = Join-Path $HOME ".ollama"
  if (Test-Path $path) {
    Remove-Item -Recurse -Force $path
    Write-Host "Purged: $path"
  }
} else {
  Write-Host "Keeping data (~\.ollama). Set OLLAMA_PURGE_DATA=1 to delete."
}
