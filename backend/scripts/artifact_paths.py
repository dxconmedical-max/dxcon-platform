"""Writable artifact directories for generated reports/API outputs.

Production and local tooling prefer ``backend/generated_*``. Some agent/CI
sandboxes cannot create files there (EPERM). Resolve a writable directory
without changing production fail-closed behavior.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _probe_writable(path: Path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".dxcon_write_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return True
    except OSError:
        return False


def _resolve(env_key: str, default_name: str) -> Path:
    override = (os.getenv(env_key) or "").strip()
    if override:
        path = Path(override).expanduser()
        path.mkdir(parents=True, exist_ok=True)
        return path

    default = ROOT / default_name
    if _probe_writable(default):
        return default

    fallback = Path(tempfile.gettempdir()) / f"dxcon_{default_name}"
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback


def generated_release_dir() -> Path:
    return _resolve("DXCON_GENERATED_RELEASE", "generated_release")


def generated_api_dir() -> Path:
    return _resolve("DXCON_GENERATED_API", "generated_api")


def generated_reports_dir() -> Path:
    return _resolve("DXCON_GENERATED_REPORTS", "generated_reports")


def uploads_dir() -> Path:
    return _resolve("DXCON_UPLOADS_DIR", "uploads")


def deployment_reports_dir() -> Path:
    """Repo-level deployment/reports, with writable fallback."""
    override = (os.getenv("DXCON_DEPLOYMENT_REPORTS") or "").strip()
    if override:
        path = Path(override).expanduser()
        path.mkdir(parents=True, exist_ok=True)
        return path
    default = ROOT.parent / "deployment" / "reports"
    if _probe_writable(default):
        return default
    fallback = Path(tempfile.gettempdir()) / "dxcon_deployment_reports"
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback
