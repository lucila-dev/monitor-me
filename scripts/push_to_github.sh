#!/bin/bash
# Push Monitor Me to GitHub without needing sudo on ~/.config
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export GH_CONFIG_DIR="${GH_CONFIG_DIR:-$HOME/Library/Application Support/gh}"
mkdir -p "$GH_CONFIG_DIR"

cd "$ROOT"

echo "Using GitHub config: $GH_CONFIG_DIR"
echo ""

if ! gh auth status >/dev/null 2>&1; then
  echo "Sign in to GitHub (choose: GitHub.com → HTTPS → Login with a web browser)"
  echo "Do NOT enter your GitHub account password in the terminal — use the browser code."
  echo ""
  gh auth login
fi

if git remote get-url origin >/dev/null 2>&1; then
  if gh repo view "$(gh api user -q .login)/monitor-me" >/dev/null 2>&1; then
    echo "Remote 'origin' already set; pushing..."
    git push -u origin main
  else
    echo "Creating GitHub repo and pushing..."
    gh repo create monitor-me \
      --public \
      --description "Monitor Me — desktop system monitor (Python, PySide6, psutil)"
    git remote set-url origin "https://github.com/$(gh api user -q .login)/monitor-me.git"
    git push -u origin main
  fi
else
  gh repo create monitor-me \
    --public \
    --source=. \
    --remote=origin \
    --push \
    --description "Monitor Me — desktop system monitor (Python, PySide6, psutil)"
fi

echo ""
echo "Done. Repo: https://github.com/$(gh api user -q .login)/monitor-me"
