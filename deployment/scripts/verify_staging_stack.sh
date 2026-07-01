#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT/backend"

echo "=== DXCON STAGING STACK VERIFY ==="
python3 scripts/verify_staging_stack.py
