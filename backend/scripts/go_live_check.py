import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

checks = [
    ["python3", "scripts/health_check.py"],
    ["python3", "scripts/check_db.py"],
    ["python3", "scripts/check_production.py"],
]

print("\n=== DXCON GO-LIVE CHECK ===\n")

for cmd in checks:
    print("RUN:", " ".join(cmd))
    result = subprocess.run(
        cmd,
        cwd=ROOT
    )

    if result.returncode != 0:
        print("\nFAILED:", " ".join(cmd))
        sys.exit(result.returncode)

print("\nALL GO-LIVE CHECKS PASSED\n")
