#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backups/postgres}"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
DATABASE_URL="${DATABASE_URL:-postgresql://dxcon:dxcon@localhost:5432/dxcon_staging}"

mkdir -p "$BACKUP_DIR"
OUTPUT="$BACKUP_DIR/dxcon-${TIMESTAMP}.sql.gz"

echo "Backing up PostgreSQL to $OUTPUT"
pg_dump "$DATABASE_URL" | gzip > "$OUTPUT"
echo "OK: backup created ($OUTPUT)"
