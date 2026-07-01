#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT/backend"

echo "=== DXCON BACKUP RESTORE VERIFY ==="
python3 - <<'PY'
import sys
from pathlib import Path

ROOT = Path(".").resolve()
sys.path.insert(0, str(ROOT))

from scripts.backup_restore_lib import run_backup_restore_verification

result = run_backup_restore_verification()
for name, payload in result["checks"].items():
    print(f"{'PASS' if payload.get('ok') else 'FAIL'}: {name}")
print(f"SUMMARY: {result['passed']}/{result['total']} passed")
if not result["ok"]:
    raise SystemExit(1)
print("BACKUP RESTORE VERIFY PASSED")
PY
