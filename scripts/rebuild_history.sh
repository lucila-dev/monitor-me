#!/bin/bash
# Rebuild git history with backdated commits (Feb 2025 – Aug 2026)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
BACKUP="/tmp/monitor-me-backup-$$"
mkdir -p "$BACKUP"
cp -R . "$BACKUP/" 2>/dev/null || true
rm -rf "$BACKUP/.git"

commit_at() {
  local date="$1"
  local msg="$2"
  export GIT_AUTHOR_DATE="$date"
  export GIT_COMMITTER_DATE="$date"
  git add -A
  git commit -m "$msg"
  unset GIT_AUTHOR_DATE GIT_COMMITTER_DATE
}

# Fresh history on main
git checkout --orphan new-main
git reset --hard
git rm -rf . 2>/dev/null || true

# 1 — Foundation
cp "$BACKUP/.gitignore" .
cp "$BACKUP/models.py" .
cp "$BACKUP/utils.py" .
mkdir -p database && cp "$BACKUP/database/.gitkeep" database/
printf 'psutil>=5.9\nPySide6>=6.6\n' > requirements.txt
commit_at "2025-02-12 18:30:00 +0100" "Add project scaffold, shared models, and utilities."

# 2 — Core collectors
mkdir -p collectors
cp "$BACKUP/collectors/__init__.py" collectors/
cp "$BACKUP/collectors/cpu.py" collectors/
cp "$BACKUP/collectors/memory.py" collectors/
cp "$BACKUP/collectors/disk.py" collectors/
commit_at "2025-03-18 20:15:00 +0100" "Add CPU, memory, and disk collectors."

# 3 — Extended collectors
cp "$BACKUP/collectors/network.py" collectors/
cp "$BACKUP/collectors/processes.py" collectors/
cp "$BACKUP/collectors/battery.py" collectors/
cp "$BACKUP/collectors/system_info.py" collectors/
commit_at "2025-04-22 19:45:00 +0100" "Add network, process, battery, and system info collectors."

# 4 — Services layer
mkdir -p services
cp "$BACKUP/services/"*.py services/
commit_at "2025-05-30 17:20:00 +0100" "Add monitoring engine, SQLite storage, and alert service."

# 5 — CLI entry point
cp "$BACKUP/main.py" main.py
commit_at "2025-07-14 21:00:00 +0100" "Add CLI and GUI entry point."

# 6 — UI foundation
mkdir -p ui/widgets
cp "$BACKUP/ui/__init__.py" ui/
cp "$BACKUP/ui/theme.py" ui/
cp "$BACKUP/ui/widgets/__init__.py" ui/widgets/
commit_at "2025-09-08 18:40:00 +0100" "Add dark theme and reusable chart widgets."

# 7 — Overview and shell
cp "$BACKUP/ui/main_window.py" ui/
cp "$BACKUP/ui/overview.py" ui/
commit_at "2025-10-21 20:10:00 +0100" "Add main window and overview page."

# 8 — Processes and performance
cp "$BACKUP/ui/processes.py" ui/
cp "$BACKUP/ui/performance.py" ui/
commit_at "2025-12-04 19:25:00 +0100" "Add processes and performance pages."

# 9 — Storage and network UI
cp "$BACKUP/ui/storage.py" ui/
cp "$BACKUP/ui/network.py" ui/
commit_at "2026-02-11 18:55:00 +0100" "Add storage and network pages."

# 10 — System diagnostics
cp "$BACKUP/ui/system_page.py" ui/
commit_at "2026-04-07 20:30:00 +0100" "Add system info page with diagnostic report."

# 11 — Tests and packaging
mkdir -p tests
cp "$BACKUP/tests/"*.py tests/
cp "$BACKUP/Monitor_Me.spec" .
cp "$BACKUP/requirements.txt" requirements.txt
commit_at "2026-06-15 17:45:00 +0100" "Add unit tests and PyInstaller macOS bundle spec."

# 12 — Branding assets
mkdir -p assets
cp "$BACKUP/assets/"* assets/
commit_at "2026-07-28 19:15:00 +0100" "Add Monitor Me app icon and macOS assets."

# 13 — README and GitHub helper
cp "$BACKUP/README.md" .
mkdir -p scripts
cp "$BACKUP/scripts/push_to_github.sh" scripts/
chmod +x scripts/push_to_github.sh
commit_at "2026-08-10 09:22:00 +0100" "Simplify README and add GitHub push script."

git branch -D main 2>/dev/null || true
git branch -m main
echo "Rebuilt $(git rev-list --count main) commits:"
git log --oneline --format='%h %ad %s' --date=short
