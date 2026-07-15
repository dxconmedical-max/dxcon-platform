#!/usr/bin/env bash
# Apply migrations 016–020 to the database pointed at by DATABASE_URL.
# Refuses common production URL markers unless STAGING_FORCE=1.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "FAIL: DATABASE_URL is required" >&2
  exit 1
fi

if [[ "${STAGING_FORCE:-}" != "1" ]]; then
  if echo "$DATABASE_URL" | grep -Eiq 'prod|production|dxcon-postgres[^_-]'; then
    echo "FAIL: DATABASE_URL looks like production. Set STAGING_FORCE=1 only after manual confirmation." >&2
    exit 1
  fi
fi

for f in \
  backend/migrations/016_lims_core.sql \
  backend/migrations/017_iot_logistics.sql \
  backend/migrations/018_analyzer_integration.sql \
  backend/migrations/019_clinical_workflow.sql \
  backend/migrations/020_patient_commerce.sql
do
  echo "Applying $f ..."
  psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "$f"
done

echo "Migrations 016–020 applied."
