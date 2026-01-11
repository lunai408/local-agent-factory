#!/usr/bin/env bash
set -euo pipefail

INFER="${OLLAMA_INFER_MODEL:-ministral-3:3b}"
EMBED="${OLLAMA_EMBED_MODEL:-nomic-embed-text}"

echo "== Pulling inference model: ${INFER} =="
ollama pull "${INFER}"

echo "== Pulling embedding model: ${EMBED} =="
ollama pull "${EMBED}"

echo "== Done. Installed models: =="
ollama list
