#!/usr/bin/env python3
"""Pre/post deployment validation."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(ROOT))

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app import create_app
from app.extensions.db import db
from app.infrastructure.infrastructure_services import InfrastructureHealthService, InfrastructureReadinessService
from app.infrastructure.runtime_validation import RuntimeValidationService
from app.runtime.runtime_config import RuntimeConfig
from deployment.pipeline.deployment_manifest import build_manifest, write_report


def verify_deployment(phase="post"):
    app = create_app()
    app.config["TESTING"] = True
    with app.app_context():
        db.create_all()
        runtime = RuntimeValidationService.validate_all(app)
        readiness = InfrastructureReadinessService.readiness(app)
        config = RuntimeConfig.load(app)
        status = InfrastructureHealthService.status(app)
    report = {
        "phase": phase,
        "runtime": runtime,
        "readiness": readiness,
        "config": config,
        "status": status,
        "manifest": build_manifest(config["profile"], config["environment"]["provider"]),
    }
    output = ROOT / "deployment" / "reports" / f"{phase}-deployment-report.json"
    write_report(output, report)
    ok = runtime["status"] != "DOWN" and readiness["ready"]
    return ok, report


def main():
    phase = sys.argv[1] if len(sys.argv) > 1 else "post"
    ok, report = verify_deployment(phase)
    print(json.dumps({"ok": ok, "phase": phase, "status": report["status"]["status"]}, indent=2))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
