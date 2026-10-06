#!/bin/bash
set -e
REPO="https://github.com/kadarek2017-coder/-Konstruktor-Wiat-3D.git"
DEST="$HOME/Konstruktor-Wiat-3D"

echo "Instalator Konstruktor Wiat 3D"
echo "=============================="

if ! command -v git >/dev/null 2>&1; then
  echo "Brak Git. macOS może poprosić o instalację narzędzi deweloperskich."
  xcode-select --install || true
  echo "Po zakończeniu instalacji uruchom ten plik ponownie."
  read -p "Naciśnij Enter, aby zakończyć..."
  exit 1
fi

if [ -d "$DEST/.git" ]; then
  echo "Program jest już zainstalowany. Aktualizuję..."
  cd "$DEST"
  git pull --ff-only
else
  if [ -e "$DEST" ]; then
    echo "Folder $DEST już istnieje, ale nie jest instalacją Git."
    echo "Zmień jego nazwę albo usuń go i uruchom instalator ponownie."
    read -p "Naciśnij Enter..."
    exit 1
  fi
  echo "Pobieram program z GitHub..."
  git clone "$REPO" "$DEST"
fi

chmod +x "$DEST/URUCHOM.command"
echo ""
echo "GOTOWE."
echo "Program znajduje się w: $DEST"
echo "Otwieram folder..."
open "$DEST"
echo "Od teraz uruchamiaj URUCHOM.command."
read -p "Naciśnij Enter, aby zakończyć..."
