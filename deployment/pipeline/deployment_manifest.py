#!/usr/bin/env python3
"""Deployment manifest helpers for Release 4.7."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
K8S_DIR = ROOT / "deployment" / "kubernetes"


def build_manifest(environment="production", provider="generic"):
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "environment": environment,
        "provider": provider,
        "kubernetes_manifests": sorted(p.name for p in K8S_DIR.glob("*.yaml")),
        "docker": {
            "dockerfile": str(ROOT / "backend" / "Dockerfile"),
            "compose": str(ROOT / "docker-compose.yml"),
        },
    }


def write_report(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return str(path)
