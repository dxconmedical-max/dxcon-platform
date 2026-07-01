#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.staging.yml}"

echo "=== DXCON STAGING BOOTSTRAP ==="
echo "Compose file: $COMPOSE_FILE"

if [[ ! -f "$COMPOSE_FILE" ]]; then
  echo "FAIL: missing $COMPOSE_FILE" >&2
  exit 1
fi

docker compose -f "$COMPOSE_FILE" build api
docker compose -f "$COMPOSE_FILE" up -d postgres redis
docker compose -f "$COMPOSE_FILE" up -d api nginx worker scheduler

echo "Waiting for API readiness..."
for _ in $(seq 1 30); do
  if docker compose -f "$COMPOSE_FILE" exec -T api curl -fsS http://127.0.0.1:8000/ready >/dev/null 2>&1; then
    echo "OK: API ready"
    break
  fi
  sleep 2
done

bash "$ROOT/deployment/scripts/verify_staging_stack.sh"
bash "$ROOT/deployment/scripts/smoke_staging.sh"

echo "STAGING BOOTSTRAP COMPLETE"
