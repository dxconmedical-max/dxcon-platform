"""Enterprise hardening pack 2 verification helpers."""

from __future__ import annotations

import ast
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
REPORT_DIR = ROOT / "generated_release"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_report(name: str, payload: dict) -> str:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORT_DIR / name
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return str(path)


def scan_python_files(base: Path):
    for path in base.rglob("*.py"):
        if any(part in {"venv", "__pycache__", ".git"} for part in path.parts):
            continue
        yield path


def check_bare_except() -> dict:
    findings = []
    pattern = re.compile(r"^\s*except\s*:\s*$")
    for path in scan_python_files(ROOT / "app"):
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if pattern.match(line):
                findings.append(f"{path.relative_to(ROOT)}:{line_no}")
    return {"ok": not findings, "count": len(findings), "findings": findings[:50]}


def check_broad_except_pass() -> dict:
    findings = []
    for path in list(scan_python_files(ROOT / "app")) + list(scan_python_files(ROOT / "scripts")):
        text = path.read_text(encoding="utf-8")
        if re.search(r"except Exception:\s*\n\s*pass", text):
            findings.append(str(path.relative_to(ROOT)))
    return {"ok": not findings, "count": len(findings), "findings": findings}


def check_bootstrap_layout() -> dict:
    required = [
        "app/bootstrap/__init__.py",
        "app/bootstrap/extensions.py",
        "app/bootstrap/middleware.py",
        "app/bootstrap/blueprints.py",
        "app/bootstrap/errors.py",
        "app/core/exceptions.py",
    ]
    missing = [item for item in required if not (ROOT / item).exists()]
    return {"ok": not missing, "missing": missing}


def check_duplicate_helper_names() -> dict:
    names = {}
    duplicates = []
    for path in scan_python_files(ROOT / "app" / "core"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                names.setdefault(node.name, []).append(str(path.relative_to(ROOT)))
    for name, paths in names.items():
        if len(paths) > 1:
            duplicates.append({"name": name, "paths": paths})
    return {"ok": len(duplicates) <= 3, "count": len(duplicates), "duplicates": duplicates[:20]}


def check_logging_standards(app) -> dict:
    import logging

    from app.core.logging_config import JsonLogFormatter, SENSITIVE_KEYS, configure_logging
    from app.core.request_context import get_correlation_id

    app.config["LOG_FORMAT"] = "json"
    configure_logging(app)
    json_ready = any(
        isinstance(getattr(handler, "formatter", None), JsonLogFormatter)
        for handler in logging.getLogger().handlers
    )
    return {
        "ok": bool(SENSITIVE_KEYS) and callable(get_correlation_id) and json_ready,
        "sensitive_keys": sorted(SENSITIVE_KEYS),
        "json_formatter": JsonLogFormatter.__name__,
    }


def check_exception_handlers(app) -> dict:
    from app.core.errors import STATUS_CODES
    from app.core.exceptions import ApiError, DxConError

    class_handlers = app.error_handler_spec.get(None, {}).get(None, {})
    has_api = ApiError in class_handlers
    return {
        "ok": has_api and issubclass(ApiError, DxConError) and 500 in STATUS_CODES,
        "status_codes": len(STATUS_CODES),
        "api_error_handler": has_api,
    }


def check_config_validation(app) -> dict:
    from app.core.config_validation import INSECURE_DEFAULTS, config_summary, validate_config

    summary = config_summary(app)
    blocked = False
    snapshot = {
        "APP_ENV": app.config.get("APP_ENV"),
        "SECRET_KEY": app.config.get("SECRET_KEY"),
        "JWT_SECRET_KEY": app.config.get("JWT_SECRET_KEY"),
        "LOG_FORMAT": app.config.get("LOG_FORMAT"),
        "CORS_ORIGINS": app.config.get("CORS_ORIGINS"),
    }
    try:
        app.config["APP_ENV"] = "production"
        app.config["SECRET_KEY"] = INSECURE_DEFAULTS["SECRET_KEY"]
        app.config["JWT_SECRET_KEY"] = INSECURE_DEFAULTS["JWT_SECRET_KEY"]
        app.config["LOG_FORMAT"] = "text"
        app.config["CORS_ORIGINS"] = "*"
        validate_config(app)
    except RuntimeError:
        blocked = True
    finally:
        app.config.update(snapshot)
    return {
        "ok": summary.get("database_configured") and INSECURE_DEFAULTS and blocked,
        "config_summary": summary,
        "production_blocks_insecure_defaults": blocked,
    }


def run_architecture_consistency_report() -> dict:
    checks = {
        "bootstrap_layout": check_bootstrap_layout(),
        "no_bare_except": check_bare_except(),
        "no_broad_except_pass": check_broad_except_pass(),
        "duplicate_helper_scan": check_duplicate_helper_names(),
    }
    report = {
        "generated_at": utc_now(),
        "release": "enterprise-hardening-pack-2",
        "checks": checks,
        "ok": all(item.get("ok") for item in checks.values()),
    }
    write_report("architecture_consistency_report.json", report)
    return report


def run_unit_tests() -> dict:
    proc = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    tail = proc.stdout.splitlines()[-3:]
    total = None
    for line in tail:
        if line.startswith("Ran "):
            try:
                total = int(line.split()[1])
            except (IndexError, ValueError):
                pass
    return {"ok": proc.returncode == 0, "exit_code": proc.returncode, "total": total, "tail": tail}


def run_blueprint_check() -> dict:
    from scripts.blueprint_registry_lib import run_blueprint_registry_verification

    return run_blueprint_registry_verification()


def run_code_quality_report() -> dict:
    checks = {"unit_tests": run_unit_tests(), "blueprint_registry": run_blueprint_check()}
    report = {
        "generated_at": utc_now(),
        "release": "enterprise-hardening-pack-2",
        "checks": checks,
        "ok": all(item.get("ok") for item in checks.values()),
    }
    write_report("code_quality_report.json", report)
    return report


def run_env_safety() -> dict:
    from scripts.env_safety_lib import run_env_safety_verification

    return run_env_safety_verification()


def run_production_standard_report(app=None) -> dict:
    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    sys.path.insert(0, str(ROOT))
    from app import create_app
    from app.extensions.db import db

    app = app or create_app()
    app.config["TESTING"] = True
    with app.app_context():
        db.create_all()
        checks = {
            "logging": check_logging_standards(app),
            "exceptions": check_exception_handlers(app),
            "config": check_config_validation(app),
            "env_safety": run_env_safety(),
        }
    report = {
        "generated_at": utc_now(),
        "release": "enterprise-hardening-pack-2",
        "checks": checks,
        "ok": all(item.get("ok") for item in checks.values()),
    }
    write_report("production_standard_report.json", report)
    return report


def run_release_isolation() -> dict:
    proc = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "release_isolation.py"),
            "check",
            "--release",
            "enterprise-hardening-pack-2",
        ],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        check=False,
    )
    return {"ok": proc.returncode == 0, "exit_code": proc.returncode, "stdout_tail": proc.stdout.splitlines()[-8:]}


def run_enterprise_hardening_verification() -> dict:
    architecture = run_architecture_consistency_report()
    quality = run_code_quality_report()
    production = run_production_standard_report()
    isolation = run_release_isolation()
    sections = {
        "architecture_consistency": architecture,
        "code_quality": quality,
        "production_standards": production,
        "release_isolation": isolation,
    }
    ok = all(section.get("ok") for section in sections.values())
    return {"ok": ok, "sections": sections}
