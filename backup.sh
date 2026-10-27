#!/bin/zsh
# Резервная копия проекта: 1) версия в истории git, 2) архив на Mac вне папки «Загрузки».
# Хранятся последние 30 архивов. Запуск: zsh backup.sh (также вызывается из publish.sh).
set -e
cd "$(dirname "$0")"
STAMP=$(date +%Y-%m-%d_%H-%M)
LOCAL_DIR="$HOME/Documents/Бэкапы финдир vercel"

# 1. История версий (site/ и deploy/ не храним — они собираются из исходников)
[ -d .git ] || git init -q
git add -A
git -c user.name="backup" -c user.email="backup@localhost" commit -qm "Резервная копия $STAMP" || true

# 2. Архив на Mac (исходники + история git)
mkdir -p "$LOCAL_DIR"
ARCHIVE="$LOCAL_DIR/findir-vercel_$STAMP.tar.gz"
tar -czf "$ARCHIVE" --exclude "./site" --exclude "./deploy" .
ls -1t "$LOCAL_DIR"/findir-vercel_*.tar.gz | tail -n +31 | while read f; do rm -f "$f"; done

echo "Резервная копия готова: $ARCHIVE"
