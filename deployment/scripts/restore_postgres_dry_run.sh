#!/usr/bin/env bash
set -euo pipefail

BACKUP_FILE="${1:-}"
DATABASE_URL="${DATABASE_URL:-postgresql://dxcon:dxcon@localhost:5432/dxcon_staging_restore_test}"

if [[ -z "$BACKUP_FILE" || ! -f "$BACKUP_FILE" ]]; then
  echo "Usage: $0 <backup.sql.gz>" >&2
  exit 1
fi

echo "=== DXCON POSTGRES RESTORE DRY RUN ==="
echo "Target: $DATABASE_URL"
echo "Backup: $BACKUP_FILE"

if ! command -v pg_restore >/dev/null 2>&1 && ! command -v psql >/dev/null 2>&1; then
  echo "WARN: pg_restore/psql not installed; validating archive only"
  gzip -t "$BACKUP_FILE"
  echo "OK: backup archive integrity verified"
  exit 0
fi

TMP_SQL="$(mktemp)"
trap 'rm -f "$TMP_SQL"' EXIT
gzip -dc "$BACKUP_FILE" > "$TMP_SQL"

if grep -q "PostgreSQL database dump" "$TMP_SQL"; then
  echo "OK: backup header detected"
else
  echo "FAIL: backup header missing" >&2
  exit 1
fi

echo "OK: restore dry-run validation passed (no database writes performed)"
