#!/usr/bin/env bash
set -euo pipefail

SOURCE="${STORAGE_PATH:-./uploads}"
BACKUP_DIR="${BACKUP_DIR:-./backups/uploads}"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
ARCHIVE="$BACKUP_DIR/uploads-${TIMESTAMP}.tar.gz"

mkdir -p "$BACKUP_DIR"

if [[ ! -d "$SOURCE" ]]; then
  echo "WARN: source path missing ($SOURCE); creating empty backup"
  mkdir -p "$SOURCE"
fi

tar -czf "$ARCHIVE" -C "$(dirname "$SOURCE")" "$(basename "$SOURCE")"
echo "OK: uploads backup created ($ARCHIVE)"
