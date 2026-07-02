#!/usr/bin/env python3
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(ROOT))
from scripts.enterprise_master_lib import run_release_isolation, utc_now, write_report

RELEASE_ID = "enterprise-hardening-pack-9"
REQUIRED_DOCS = (
    "docs/ARCHITECTURE.md",
    "docs/MODULES.md",
    "docs/API_REFERENCE.md",
    "docs/DEPLOYMENT.md",
    "docs/OPERATIONS.md",
    "docs/BACKUP.md",
    "docs/RESTORE.md",
    "docs/RUNBOOK.md",
    "docs/DISASTER_RECOVERY.md",
)

def main():
    missing = [doc for doc in REQUIRED_DOCS if not (REPO / doc).exists()]
    ok = not missing
    write_report("documentation_review.json", {
        "generated_at": utc_now(),
        "release": RELEASE_ID,
        "required_docs": list(REQUIRED_DOCS),
        "missing": missing,
        "ok": ok,
    })
    print("\n=== DXCON ENTERPRISE PACK 9 - DOCUMENTATION ===\n")
    print(f"{'PASS' if ok else 'FAIL'}: documentation_files")
    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
