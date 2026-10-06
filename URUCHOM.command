#!/bin/bash
cd "$(dirname "$0")"

echo "Konstruktor Wiat 3D"
echo "==================="
if [ -d ".git" ] && command -v git >/dev/null 2>&1; then
  echo "Sprawdzam aktualizacje z GitHub..."
  git pull --ff-only
fi

if [ ! -d ".venv" ]; then
  echo "Pierwsze uruchomienie - przygotowuję środowisko..."
  python3 -m venv .venv
  source .venv/bin/activate
  python -m pip install --upgrade pip
  pip install -r requirements.txt
else
  source .venv/bin/activate
  pip install -q -r requirements.txt
fi

echo "Uruchamiam program..."
streamlit run app.py
