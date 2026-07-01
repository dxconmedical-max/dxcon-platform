#!/usr/bin/env python3
"""Deployment orchestration entrypoint."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PIPELINE = ROOT / "deployment" / "pipeline"


def main():
    steps = [
        ["python3", str(PIPELINE / "verify_deployment.py"), "pre"],
        ["python3", str(ROOT / "backend" / "scripts" / "verify_deployment_readiness.py")],
        ["python3", str(PIPELINE / "verify_deployment.py"), "post"],
    ]
    results = []
    for cmd in steps:
        proc = subprocess.run(cmd, cwd=str(ROOT))
        results.append({"command": cmd, "exit_code": proc.returncode})
        if proc.returncode != 0:
            print(json.dumps({"ok": False, "results": results}, indent=2))
            sys.exit(proc.returncode)
    print(json.dumps({"ok": True, "results": results}, indent=2))


if __name__ == "__main__":
    main()
