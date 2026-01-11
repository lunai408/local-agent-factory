$ErrorActionPreference = "Stop"

$infer = $env:OLLAMA_INFER_MODEL
if (-not $infer) { $infer = "ministral-3:3b" }

$embed = $env:OLLAMA_EMBED_MODEL
if (-not $embed) { $embed = "nomic-embed-text" }

Write-Host "== Pulling inference model: $infer =="
ollama pull $infer

Write-Host "== Pulling embedding model: $embed =="
ollama pull $embed

ollama list
