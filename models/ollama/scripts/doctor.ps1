$ErrorActionPreference = "Stop"

# Utilise OLLAMA_HOST pour coherence avec start.ps1
$OllamaHost = if ($env:OLLAMA_HOST) { $env:OLLAMA_HOST } else { "127.0.0.1:11434" }
$BaseUrl = "http://$OllamaHost"

Write-Host "== Ollama doctor =="
Write-Host "BASE: $BaseUrl"

try {
    $response = Invoke-WebRequest -Uri "$BaseUrl/api/tags" -UseBasicParsing -TimeoutSec 5
    Write-Host "Ollama reachable"
    $content = $response.Content
    if ($content.Length -gt 400) {
        $content = $content.Substring(0, 400)
    }
    Write-Host $content
} catch {
    Write-Host "Ollama not reachable at $BaseUrl"
    Write-Host "Try: task ollama:start"
    exit 1
}
