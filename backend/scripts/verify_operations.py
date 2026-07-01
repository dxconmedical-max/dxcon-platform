import os
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from app.operations.job_registry import JobRegistry
from app.operations.scheduler_service import SchedulerService
from scripts.seed_operations_demo import seed_operations_demo


CHECKS = []


def _payload(response):
    body = response.get_json() or {}
    if isinstance(body.get("data"), dict) and "success" in body:
        return body["data"]
    return body


def check(name, ok):
    CHECKS.append((name, ok))
    print(f"{'PASS' if ok else 'FAIL'}: {name}")
    return ok


def verify_imports():
    modules = [
        "app.operations.scheduler_service",
        "app.operations.backup_service",
        "app.operations.restore_service",
        "app.operations.maintenance_service",
        "app.operations.secret_rotation_service",
        "app.operations.deployment_service",
        "app.operations.queue_operations_service",
        "app.models.operations_platform",
    ]
    ok = True
    for module in modules:
        try:
            __import__(module)
            print("OK: import", module)
        except Exception as exc:
            print("FAIL:", module, exc)
            ok = False
    return check("imports", ok)


def verify_routes(app):
    required = [
        "/api/v1/operations/jobs",
        "/api/v1/operations/backups",
        "/api/v1/operations/backups/run",
        "/api/v1/operations/restores/dry-run",
        "/api/v1/operations/maintenance",
        "/api/v1/operations/secrets",
        "/api/v1/operations/deployment",
        "/api/v1/operations/queues/dead-letters",
        "/operations",
        "/operations/jobs",
        "/operations/backups",
        "/operations/maintenance",
        "/operations/secrets",
        "/operations/deployment",
        "/operations/queues",
    ]
    routes = {str(rule) for rule in app.url_map.iter_rules()}
    missing = [route for route in required if route not in routes]
    for route in required:
        if route in routes:
            print("OK:", route)
    if missing:
        print("MISSING:", missing)
    return check("routes", not missing)


def verify_no_duplicate_routes(app):
    prefixes = ("/api/v1/operations", "/operations")
    seen = defaultdict(list)
    for rule in app.url_map.iter_rules():
        path = str(rule.rule)
        if not any(path == p or path.startswith(p + "/") for p in prefixes):
            continue
        key = (path, tuple(sorted(m for m in rule.methods if m not in {"HEAD", "OPTIONS"})))
        seen[key].append(rule.endpoint)
    duplicates = {key: endpoints for key, endpoints in seen.items() if len(endpoints) > 1}
    if duplicates:
        print("DUPLICATE:", duplicates)
        return check("no duplicate routes", False)
    print("OK: no duplicate operations routes")
    return check("no duplicate routes", True)


def verify_scheduler_registry():
    JobRegistry.initialize()
    ok = len(JobRegistry.list_handlers()) >= 4
    return check("scheduler registry", ok)


def verify_manual_job_run(client):
    SchedulerService.ensure_defaults()
    jobs = _payload(client.get("/api/v1/operations/jobs"))["jobs"]
    job_id = jobs[0]["id"]
    response = client.post(f"/api/v1/operations/jobs/{job_id}/run")
    return check("manual job run", response.status_code == 200)


def verify_backup_metadata(client):
    response = client.post("/api/v1/operations/backups/run", json={"backup_type": "DATABASE"})
    body = _payload(response)
    ok = response.status_code == 201 and "artifact" in body and body["artifact"].get("checksum")
    return check("backup metadata", ok)


def verify_restore_dry_run(client):
    backup_id = _payload(client.post("/api/v1/operations/backups/run", json={"backup_type": "STORAGE"}))["backup"]["id"]
    response = client.post("/api/v1/operations/restores/dry-run", json={"backup_id": backup_id})
    body = _payload(response)
    ok = response.status_code == 201 and body["restore"]["mode"] == "DRY_RUN"
    return check("restore dry-run", ok)


def verify_maintenance_mode(client):
    enable = client.post("/api/v1/operations/maintenance/enable", json={"title": "Verify maintenance"})
    disable = client.post("/api/v1/operations/maintenance/disable")
    ok = enable.status_code == 200 and disable.status_code == 200
    return check("maintenance mode", ok)


def verify_secret_validation(client):
    response = client.post("/api/v1/operations/secrets/validate")
    ok = response.status_code == 200 and "validated" in _payload(response)
    return check("secret validation", ok)


def verify_deployment_readiness(client):
    response = client.post("/api/v1/operations/deployment/check")
    ok = response.status_code == 201 and "deployment" in _payload(response)
    return check("deployment readiness", ok)


def verify_queue_operations(client):
    summary = client.get("/api/v1/operations/queues")
    dead = client.get("/api/v1/operations/queues/dead-letters")
    ok = summary.status_code == 200 and dead.status_code == 200
    return check("queue operations", ok)


def verify_dashboard(client):
    pages = (
        "/operations",
        "/operations/jobs",
        "/operations/backups",
        "/operations/maintenance",
        "/operations/secrets",
        "/operations/deployment",
        "/operations/queues",
    )
    ok = all(client.get(page).status_code == 200 for page in pages)
    return check("dashboard routes", ok)


def verify_seed():
    result = seed_operations_demo()
    ok = result.get("jobs", 0) >= 4 and result.get("backups", 0) >= 2
    return check("demo seed", ok)


def verify_release_isolation():
    if os.environ.get("DXCON_RC2_REGRESSION"):
        return check("release isolation", True)
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "release_isolation.py"), "check", "--release", "4.6"],
        cwd=str(ROOT.parent),
        capture_output=True,
        text=True,
    )
    print(proc.stdout)
    if proc.stderr:
        print(proc.stderr)
    return check("release isolation", proc.returncode == 0)


def main():
    app = create_app()
    with app.app_context():
        db.create_all()
        verify_imports()
        verify_routes(app)
        verify_no_duplicate_routes(app)
        verify_scheduler_registry()
        client = app.test_client()
        verify_manual_job_run(client)
        verify_backup_metadata(client)
        verify_restore_dry_run(client)
        verify_maintenance_mode(client)
        verify_secret_validation(client)
        verify_deployment_readiness(client)
        verify_queue_operations(client)
        verify_dashboard(client)
        verify_seed()
    verify_release_isolation()

    failed = [name for name, ok in CHECKS if not ok]
    print("\nSUMMARY:", len(CHECKS) - len(failed), "passed,", len(failed), "failed")
    if failed:
        print("FAILED:", failed)
        return 1
    print("ALL CHECKS PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
