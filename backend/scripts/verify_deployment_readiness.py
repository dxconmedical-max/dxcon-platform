import os
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(REPO))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from app.infrastructure.recovery_service import RecoveryService
from app.infrastructure.scaling_advisor import ScalingAdvisor
from app.runtime.deployment_profile import PROFILES
from deployment.pipeline.deployment_manifest import build_manifest


CHECKS = []


def check(name, ok):
    CHECKS.append((name, ok))
    print(f"{'PASS' if ok else 'FAIL'}: {name}")
    return ok


def verify_runtime_profiles():
    ok = set(PROFILES) == {"development", "staging", "production", "testing"}
    for profile in PROFILES:
        print("OK: profile", profile)
    return check("runtime profiles", ok)


def verify_docker():
    dockerfile = ROOT / "Dockerfile"
    compose = REPO / "docker-compose.yml"
    text = dockerfile.read_text(encoding="utf-8") if dockerfile.exists() else ""
    ok = dockerfile.exists() and compose.exists()
    ok = ok and "HEALTHCHECK" in text and "USER" in text and "/live" in text
    if ok:
        print("OK: Dockerfile hardened")
        print("OK: docker-compose.yml present")
    return check("Docker validation", ok)


def verify_kubernetes():
    k8s = REPO / "deployment" / "kubernetes"
    required = [
        "namespace.yaml",
        "deployment.yaml",
        "service.yaml",
        "ingress.yaml",
        "configmap.yaml",
        "secret.example.yaml",
        "hpa.yaml",
        "network-policy.yaml",
        "pdb.yaml",
    ]
    missing = [name for name in required if not (k8s / name).exists()]
    for name in required:
        if name not in missing:
            print("OK:", name)
    if missing:
        print("MISSING:", missing)
    return check("Kubernetes manifests", not missing)


def verify_pipeline():
    pipeline = REPO / "deployment" / "pipeline"
    required = ["deploy.py", "verify_deployment.py", "rollback.py", "deployment_manifest.py"]
    missing = [name for name in required if not (pipeline / name).exists()]
    manifest = build_manifest("testing", "generic")
    ok = not missing and bool(manifest["kubernetes_manifests"])
    if missing:
        print("MISSING:", missing)
    else:
        print("OK: deployment pipeline scripts")
    return check("deployment pipeline", ok)


def verify_infrastructure(app):
    client = app.test_client()
    status = client.get("/api/v1/infrastructure/status")
    readiness = client.get("/api/v1/infrastructure/readiness")
    config = client.get("/api/v1/infrastructure/config")
    ok = all(resp.status_code in {200, 503} for resp in (status, readiness, config))
    ok = ok and status.get_json().get("status") is not None
    if ok:
        print("OK: infrastructure status/readiness/config")
    return check("infrastructure status", ok)


def verify_recovery(app):
    with app.app_context():
        db.create_all()
        RecoveryService.ensure_defaults()
        summary = RecoveryService.summary()
    ok = summary["plans"] >= 1
    if ok:
        print("OK: recovery metadata", summary)
    return check("recovery metadata", ok)


def verify_scaling(app):
    with app.app_context():
        advice = ScalingAdvisor.recommend(app)
    ok = "workers" in advice and "database_pool" in advice
    if ok:
        print("OK: scaling advisor")
    return check("scaling advisor", ok)


def verify_dashboard_routes(app):
    required = [
        "/deployment",
        "/deployment/readiness",
        "/deployment/runtime",
        "/deployment/scaling",
        "/deployment/recovery",
    ]
    routes = {str(rule) for rule in app.url_map.iter_rules()}
    missing = [route for route in required if route not in routes]
    for route in required:
        if route in routes:
            print("OK:", route)
    if missing:
        print("MISSING:", missing)
    return check("dashboard routes", not missing)


def verify_no_duplicate_routes(app):
    prefixes = ("/api/v1/infrastructure", "/deployment")
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
    print("OK: no duplicate infrastructure/deployment routes")
    return check("no duplicate routes", True)


def main():
    print("\n=== DXCON DEPLOYMENT READINESS VERIFY ===\n")
    verify_runtime_profiles()
    verify_docker()
    verify_kubernetes()
    verify_pipeline()

    app = create_app()
    app.config["TESTING"] = True
    with app.app_context():
        db.create_all()
    verify_infrastructure(app)
    verify_recovery(app)
    verify_scaling(app)
    verify_dashboard_routes(app)
    verify_no_duplicate_routes(app)

    failed = [name for name, ok in CHECKS if not ok]
    print("\nSUMMARY:", len(CHECKS) - len(failed), "passed,", len(failed), "failed")
    if failed:
        print("FAILED:", failed)
        sys.exit(1)
    print("ALL CHECKS PASSED")
    sys.exit(0)


if __name__ == "__main__":
    main()
