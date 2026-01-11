#!/usr/bin/env bash
set -euo pipefail

OS="$(uname -s)"

echo "== Uninstall Ollama ($OS) =="

# Stop first (best effort)
if command -v ollama >/dev/null 2>&1; then
  pkill -f ollama || true
fi

if [[ "$OS" == "Darwin" ]]; then
  # brew uninstall if present
  if command -v brew >/dev/null 2>&1 && brew list --formula 2>/dev/null | grep -q '^ollama$'; then
    echo "Removing Ollama (brew)..."
    brew uninstall ollama || true
  fi

  # Remove Ollama.app if installed (common path)
  if [ -d "/Applications/Ollama.app" ]; then
    echo "Removing /Applications/Ollama.app ..."
    rm -rf "/Applications/Ollama.app"
  fi

  # Remove LaunchAgent if exists (best effort)
  if [ -f "$HOME/Library/LaunchAgents/com.ollama.ollama.plist" ]; then
    launchctl unload "$HOME/Library/LaunchAgents/com.ollama.ollama.plist" || true
    rm -f "$HOME/Library/LaunchAgents/com.ollama.ollama.plist"
  fi

  # Remove data (ASK: destructive)
  if [ "${OLLAMA_PURGE_DATA:-0}" = "1" ]; then
    echo "Purging Ollama data (~/.ollama)..."
    rm -rf "$HOME/.ollama"
  else
    echo "Keeping data at ~/.ollama (set OLLAMA_PURGE_DATA=1 to delete)."
  fi

elif [[ "$OS" == "Linux" ]]; then
  # systemd service (if installed that way)
  if command -v systemctl >/dev/null 2>&1; then
    sudo systemctl stop ollama 2>/dev/null || true
    sudo systemctl disable ollama 2>/dev/null || true
  fi

  # remove binary (typical install.sh location)
  if [ -f "/usr/local/bin/ollama" ]; then
    echo "Removing /usr/local/bin/ollama ..."
    sudo rm -f /usr/local/bin/ollama
  fi

  # remove service files (best effort)
  sudo rm -f /etc/systemd/system/ollama.service 2>/dev/null || true
  sudo systemctl daemon-reload 2>/dev/null || true

  if [ "${OLLAMA_PURGE_DATA:-0}" = "1" ]; then
    echo "Purging Ollama data (~/.ollama)..."
    rm -rf "$HOME/.ollama"
  else
    echo "Keeping data at ~/.ollama (set OLLAMA_PURGE_DATA=1 to delete)."
  fi
else
  echo "Unsupported OS: $OS"
  exit 1
fi

echo "== Done =="
