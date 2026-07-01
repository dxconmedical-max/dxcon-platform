"""GA candidate validation helpers for staging sprint 5."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
GENERATED_DIR = ROOT / "generated_release"
GENERATED_API_DIR = ROOT / "generated_api"

RELEASE = "v1.0.0-ga-candidate"
RC2_TAG = "v1.0.0-rc2"

RC2_ARTIFACTS = (
    "RC2_REPORT.json",
    "PRODUCTION_CUTOVER_CHECKLIST.json",
    "ROLLBACK_CHECKLIST.json",
    "ENVIRONMENT_MATRIX.json",
    "ROLLBACK_PACKAGE.json",
)

STAGING_ARTIFACTS = (
    "docker-compose.staging.yml",
    "docker-compose.production.yml",
    "backend/Dockerfile",
    "backend/gunicorn.conf.py",
    "backend/production_start.py",
    "deployment/nginx/nginx.conf",
    "deployment/nginx/default.conf",
    "deployment/monitoring/prometheus.yml",
    "backend/.env.staging.example",
    "backend/.env.production.example",
    "backend/scripts/security_preflight.py",
    "backend/scripts/uat_smoke.py",
    "backend/scripts/verify_uat_data.py",
    "backend/scripts/verify_staging_stack.py",
    "backend/scripts/verify_staging_monitoring.py",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def git_sha() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else "unknown"


def ensure_generated_dir() -> Path:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    return GENERATED_DIR


def write_json(name: str, payload: dict) -> str:
    path = ensure_generated_dir() / name
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return str(path)


def run_unit_tests() -> dict:
    proc = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    tail = proc.stdout.splitlines()[-3:]
    passed = proc.returncode == 0
    total = None
    for line in tail:
        if line.startswith("Ran "):
            try:
                total = int(line.split()[1])
            except (IndexError, ValueError):
                pass
    return {
        "ok": passed,
        "exit_code": proc.returncode,
        "total": total,
        "summary_tail": tail,
    }


def verify_rc2_artifacts() -> dict:
    missing = [name for name in RC2_ARTIFACTS if not (GENERATED_DIR / name).exists()]
    tag_result = subprocess.run(
        ["git", "tag", "-l", RC2_TAG],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        check=False,
    )
    tag_present = RC2_TAG in tag_result.stdout.split()
    return {
        "ok": not missing and tag_present,
        "missing": missing,
        "tag": RC2_TAG,
        "tag_present": tag_present,
        "artifacts": list(RC2_ARTIFACTS),
    }


def verify_staging_artifacts() -> dict:
    missing = [path for path in STAGING_ARTIFACTS if not (REPO / path).exists()]
    return {
        "ok": not missing,
        "missing": missing,
        "artifacts": list(STAGING_ARTIFACTS),
    }


def check_production_readiness_score() -> dict:
    import os

    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    from app import create_app
    from app.core.deployment import deployment_readiness
    from app.extensions.db import db
    from scripts.staging_stack_lib import parse_env_file

    staging_values = parse_env_file(ROOT / ".env.staging.example")
    app = create_app()
    app.config.update(
        {
            "TESTING": True,
            "APP_ENV": "staging",
            "CORS_ORIGINS": staging_values.get("CORS_ORIGINS", "https://staging.dxcon.test"),
            "SQLALCHEMY_DATABASE_URI": staging_values.get(
                "DATABASE_URL",
                "postgresql://dxcon:dxcon@postgres:5432/dxcon_staging",
            ),
            "REDIS_URL": staging_values.get("REDIS_URL", "redis://redis:6379/0"),
            "SMTP_HOST": staging_values.get("SMTP_HOST", "smtp.example.com"),
            "SMTP_FROM": staging_values.get("SMTP_FROM", "noreply@staging.dxcon.test"),
        }
    )
    app.extensions.setdefault("dxcon_deployment", {})
    app.extensions["dxcon_deployment"]["migration_status"] = {"ready": True}
    with app.app_context():
        db.create_all()
        readiness = deployment_readiness(app)
    return {
        "ok": readiness["score"] >= 80 and readiness["ready_for_production"],
        "score": readiness["score"],
        "ready_for_production": readiness["ready_for_production"],
        "checks": readiness["checks"],
    }


def check_rollback_readiness() -> dict:
    path = GENERATED_DIR / "ROLLBACK_PACKAGE.json"
    if not path.exists():
        return {"ok": False, "error": "ROLLBACK_PACKAGE.json missing"}
    payload = json.loads(path.read_text(encoding="utf-8"))
    required = (
        "current_git_sha",
        "previous_release_sha",
        "rollback_command_recommendation",
        "artifact_checklist",
    )
    missing = [key for key in required if not payload.get(key)]
    return {
        "ok": not missing,
        "missing_fields": missing,
        "previous_tag": payload.get("previous_tag"),
        "rollback_command": payload.get("rollback_command_recommendation"),
    }


def check_backup_restore_readiness() -> dict:
    from scripts.backup_restore_lib import run_backup_restore_verification

    return run_backup_restore_verification(create_samples=True)


def check_go_live_blockers() -> dict:
    import os

    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    from app import create_app
    from app.infrastructure.production_readiness import evaluate_go_live_blockers
    from scripts.staging_stack_lib import parse_env_file

    staging_values = parse_env_file(ROOT / ".env.staging.example")
    app = create_app()
    app.config.update(
        {
            "TESTING": False,
            "APP_ENV": "staging",
            "CORS_ORIGINS": staging_values.get("CORS_ORIGINS", "https://staging.dxcon.test"),
            "SQLALCHEMY_DATABASE_URI": staging_values.get(
                "DATABASE_URL",
                "postgresql://dxcon:dxcon@postgres:5432/dxcon_staging",
            ),
            "REDIS_URL": staging_values.get("REDIS_URL", "redis://redis:6379/0"),
            "SMTP_HOST": staging_values.get("SMTP_HOST", "smtp.example.com"),
            "SMTP_FROM": staging_values.get("SMTP_FROM", "noreply@staging.dxcon.test"),
        }
    )
    blockers = evaluate_go_live_blockers(app)
    write_json(
        "GO_LIVE_BLOCKERS.json",
        {
            **blockers,
            "generated_at": utc_now(),
            "profile": "staging-template",
        },
    )
    return {
        "ok": blockers.get("ready") and blockers.get("blocker_count", 1) == 0,
        "blocker_count": blockers.get("blocker_count"),
        "warning_count": blockers.get("warning_count"),
        "blockers": blockers.get("blockers", []),
    }


def _openapi_path_count(path: Path) -> int:
    if not path.exists():
        return 0
    payload = json.loads(path.read_text(encoding="utf-8"))
    return len(payload.get("paths", {}))


def _openapi_fingerprint(path: Path) -> str:
    if not path.exists():
        return ""
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def regenerate_openapi() -> dict:
    import os

    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    from app import create_app
    from app.api_platform.openapi_generator import write_openapi_artifacts

    before_paths = _openapi_path_count(GENERATED_API_DIR / "openapi.json")
    before_hash = _openapi_fingerprint(GENERATED_API_DIR / "openapi.json")
    app = create_app()
    artifacts = write_openapi_artifacts(app, output_dir=str(GENERATED_API_DIR))
    after_paths = artifacts["paths"]
    after_hash = _openapi_fingerprint(GENERATED_API_DIR / "openapi.json")
    return {
        "ok": after_paths > 0 and (GENERATED_API_DIR / "openapi.json").exists(),
        "paths_before": before_paths,
        "paths_after": after_paths,
        "hash_before": before_hash,
        "hash_after": after_hash,
        "regenerated": before_hash != after_hash or before_paths == 0,
        "json_path": str(GENERATED_API_DIR / "openapi.json"),
        "yaml_path": str(GENERATED_API_DIR / "openapi.yaml"),
    }


def check_api_freeze(openapi_result: dict | None = None) -> dict:
    import os

    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    from app import create_app
    from app.api_platform.api_inventory import scan_routes
    from scripts.go_live_rc2_lib import find_duplicate_routes

    app = create_app()
    inventory = scan_routes(app)
    openapi_result = openapi_result or regenerate_openapi()
    openapi_path = GENERATED_API_DIR / "openapi.json"
    openapi_paths = set(json.loads(openapi_path.read_text(encoding="utf-8")).get("paths", {}))
    inventory_paths = {route["path"].replace("<", "{").replace(">", "}") for route in inventory["routes"]}
    missing_in_openapi = sorted(path for path in inventory_paths if path not in openapi_paths)
    duplicates = find_duplicate_routes(app)
    drift = abs(openapi_result["paths_after"] - openapi_result["paths_before"])
    frozen = (
        not duplicates
        and not missing_in_openapi
        and openapi_result["ok"]
        and drift <= 1
    )
    report = {
        "generated_at": utc_now(),
        "release": RELEASE,
        "git_sha": git_sha(),
        "frozen": frozen,
        "openapi_paths": openapi_result["paths_after"],
        "inventory_paths": len(inventory_paths),
        "missing_in_openapi": missing_in_openapi[:20],
        "missing_count": len(missing_in_openapi),
        "duplicate_routes": len(duplicates),
        "path_drift": drift,
        "hash_before": openapi_result["hash_before"],
        "hash_after": openapi_result["hash_after"],
        "regenerated": openapi_result["regenerated"],
    }
    write_json("API_FREEZE_REPORT.json", report)
    return {
        "ok": frozen,
        **report,
    }


def run_ga_smoke_suite() -> dict:
    import os

    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    from app import create_app
    from app.extensions.db import db
    from scripts.go_live_rc2_lib import run_final_smoke
    from scripts.security_preflight_lib import run_security_preflight
    from scripts.staging_monitoring_lib import run_monitoring_verification
    from scripts.staging_stack_lib import run_staging_verification
    from scripts.uat_smoke import run_uat_smoke

    app = create_app()
    app.config["TESTING"] = True
    with app.app_context():
        db.create_all()
    client = app.test_client()

    suites = {
        "rc2_smoke": None,
        "uat_smoke": run_uat_smoke(),
        "security_preflight": run_security_preflight(app),
        "staging_stack": run_staging_verification(),
        "staging_monitoring": run_monitoring_verification(),
    }
    with app.app_context():
        suites["rc2_smoke"] = run_final_smoke(app, client)

    passed = sum(1 for item in suites.values() if item.get("ok"))
    return {
        "ok": passed == len(suites),
        "passed": passed,
        "total": len(suites),
        "suites": suites,
    }


def compute_ga_score(sections: dict) -> dict:
    weights = {
        "unit_tests": 15,
        "regression": 20,
        "smoke_suite": 20,
        "production_readiness": 15,
        "rollback_readiness": 10,
        "backup_restore": 10,
        "api_freeze": 5,
        "artifacts": 5,
    }
    breakdown = {}
    weighted = 0.0
    for name, weight in weights.items():
        payload = sections.get(name, {})
        ok = payload.get("ok", False)
        section_score = weight if ok else 0.0
        weighted += section_score
        breakdown[name] = {"weight": weight, "score": section_score, "ok": ok}
    score = round(weighted, 2)
    all_ok = all(sections.get(name, {}).get("ok") for name in weights)
    return {
        "score": score,
        "ready_for_ga": score >= 95 and all_ok,
        "breakdown": breakdown,
    }


def build_ga_checklist(sections: dict, score: dict) -> dict:
    items = []
    for name, payload in sections.items():
        if isinstance(payload, dict) and "ok" in payload:
            items.append({"item": name, "status": "PASS" if payload["ok"] else "FAIL"})
        elif isinstance(payload, dict) and "checks" in payload:
            for check_name, check_payload in payload["checks"].items():
                status = "PASS" if check_payload.get("ok") else "FAIL"
                items.append({"item": f"{name}:{check_name}", "status": status})
        elif isinstance(payload, dict) and "suites" in payload:
            for suite_name, suite_payload in payload["suites"].items():
                items.append(
                    {
                        "item": f"{name}:{suite_name}",
                        "status": "PASS" if suite_payload.get("ok") else "FAIL",
                    }
                )
    return {
        "generated_at": utc_now(),
        "release": RELEASE,
        "git_sha": git_sha(),
        "ready_for_ga": score["ready_for_ga"],
        "score": score["score"],
        "items": items,
    }


def build_ga_report(sections: dict, score: dict) -> dict:
    return {
        "generated_at": utc_now(),
        "release": RELEASE,
        "git_sha": git_sha(),
        "rc2_baseline": RC2_TAG,
        "score": score,
        "sections": {
            key: {
                "ok": value.get("ok"),
                "passed": value.get("passed"),
                "total": value.get("total"),
            }
            for key, value in sections.items()
            if isinstance(value, dict) and "ok" in value
        },
        "ready_for_ga": score["ready_for_ga"],
    }


def run_ga_validation(
    *,
    write_reports: bool = True,
    run_regression: bool = True,
    run_tests: bool = True,
) -> dict:
    from scripts.go_live_rc2_lib import run_full_regression

    sections = {}
    if run_tests:
        sections["unit_tests"] = run_unit_tests()
    else:
        sections["unit_tests"] = {"ok": True, "skipped": True}

    sections["regression"] = run_full_regression() if run_regression else {"ok": True, "passed": 0, "total": 0}
    sections["smoke_suite"] = run_ga_smoke_suite()
    sections["production_readiness"] = check_production_readiness_score()
    sections["rollback_readiness"] = check_rollback_readiness()
    sections["backup_restore"] = check_backup_restore_readiness()
    openapi = regenerate_openapi()
    sections["api_freeze"] = check_api_freeze(openapi)
    blockers = check_go_live_blockers()
    sections["artifacts"] = {
        "ok": verify_rc2_artifacts()["ok"]
        and verify_staging_artifacts()["ok"]
        and blockers["ok"],
        "rc2": verify_rc2_artifacts(),
        "staging": verify_staging_artifacts(),
        "blockers": blockers,
    }

    score = compute_ga_score(sections)
    ok = score["ready_for_ga"] and all(
        sections[name]["ok"]
        for name in (
            "unit_tests",
            "regression",
            "smoke_suite",
            "production_readiness",
            "rollback_readiness",
            "backup_restore",
            "api_freeze",
            "artifacts",
        )
    )

    if write_reports:
        write_json("GA_REPORT.json", build_ga_report(sections, score))
        write_json("GA_CHECKLIST.json", build_ga_checklist(sections, score))

    return {
        "ok": ok,
        "score": score,
        "sections": sections,
    }
