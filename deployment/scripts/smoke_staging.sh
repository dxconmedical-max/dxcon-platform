#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT/backend"

echo "=== DXCON STAGING SMOKE ==="
python3 scripts/smoke_test_staging_stack.py
