$ErrorActionPreference = "Stop"

$OllamaHost = if ($env:OLLAMA_HOST) { $env:OLLAMA_HOST } else { "127.0.0.1:11434" }

Write-Host "== Starting Ollama daemon =="

# Check if already running
try {
    $null = Invoke-WebRequest -Uri "http://$OllamaHost/api/tags" -UseBasicParsing -TimeoutSec 3
    Write-Host "Ollama already running on $OllamaHost"
    exit 0
} catch {
    # Not running, continue to start
}

# Start Ollama in background
$env:OLLAMA_HOST = $OllamaHost
Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden

Write-Host "Ollama starting on $OllamaHost..."
