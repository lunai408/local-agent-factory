#!/usr/bin/env bash
set -euo pipefail

HOST="${OLLAMA_HOST:-127.0.0.1:11434}"

echo "== Starting Ollama daemon =="
# Sur Mac, Ollama tourne souvent via l’app. Sur Linux, `ollama serve` suffit.
# On lance en background si ce n'est pas déjà up.
if curl -fsS "http://${HOST}/api/tags" >/dev/null 2>&1; then
  echo "Ollama already running on ${HOST}"
  exit 0
fi

# Démarrage
OLLAMA_HOST="http://${HOST}" ollama serve >/tmp/ollama.log 2>&1 & disown

echo "Ollama starting... logs: /tmp/ollama.log"
