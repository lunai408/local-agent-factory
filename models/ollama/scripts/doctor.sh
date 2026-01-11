#!/usr/bin/env bash
set -euo pipefail

# Utilise OLLAMA_HOST pour coherence avec start.sh
HOST="${OLLAMA_HOST:-127.0.0.1:11434}"
BASE="http://${HOST}"

echo "== Ollama doctor =="
echo "BASE: ${BASE}"

if curl -fsS "${BASE}/api/tags" >/dev/null 2>&1; then
  echo "✅ Ollama reachable"
  curl -fsS "${BASE}/api/tags" | head -c 400 || true
else
  echo "❌ Ollama not reachable at ${BASE}"
  echo "Try: task ollama:start"
  exit 1
fi
