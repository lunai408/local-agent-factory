#!/usr/bin/env bash
set -euo pipefail

OS="$(uname -s)"
echo "== Installing Ollama for $OS =="

if [[ "$OS" == "Darwin" ]]; then
  # macOS: méthode recommandée = installer l’app Ollama (UI) ou via Homebrew cask si dispo
  # On tente brew d'abord, sinon on indique l'install standard.
  if command -v brew >/dev/null 2>&1; then
    echo "Using Homebrew..."
    brew install ollama || true
    # Certaines configs utilisent un cask/app ; si brew ne marche pas, l’utilisateur peut installer via le site Ollama.
  else
    echo "Homebrew not found. Install Ollama from the official installer (recommended on macOS)."
    echo "Then re-run: ./models/ollama/doctor.sh"
  fi

elif [[ "$OS" == "Linux" ]]; then
  # Linux: installer via script officiel
  curl -fsSL https://ollama.com/install.sh | sh
else
  echo "Unsupported OS: $OS"
  exit 1
fi

echo "== Done =="
