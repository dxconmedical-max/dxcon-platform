import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["FEDERATION_SEED_LABS"] = "10"
os.environ["FEDERATION_SEED_BRANCHES"] = "20"
os.environ["FEDERATION_SEED_CAPABILITIES"] = "40"
os.environ["FEDERATION_SEED_CAPACITY_DAYS"] = "7"
os.environ["FEDERATION_SEED_ROUTING"] = "20"
os.environ["FEDERATION_SEED_FAILOVER"] = "5"

from app import create_app
from app.extensions.db import db
from app.models.federation_capacity import (
    AnalyzerCapacity,
    CapacityRule,
    CapacitySnapshot,
    LabWorkloadSnapshot,
)
from app.models.federation_core import (
    FederatedLab,
    FederationCapability,
    FederationEvent,
    FederationPolicy,
    FederationProvider,
    FederationProviderBranch,
)
from app.models.federation_failover import FailoverEvent, FailoverRule
from app.models.federation_routing import RoutingAudit, RoutingDecision, RoutingRule
from app.services.federation_capacity_service import CapacityCalculatorService
from app.services.federation_failover_service import FailoverService
from app.services.federation_routing_service import SmartRoutingService
from scripts.seed_federation_demo import seed_federation_demo


def verify_models_import():
    models = [
        FederatedLab,
        FederationProvider,
        FederationProviderBranch,
        FederationCapability,
        FederationPolicy,
        FederationEvent,
        CapacitySnapshot,
        CapacityRule,
        AnalyzerCapacity,
        LabWorkloadSnapshot,
        RoutingRule,
        RoutingDecision,
        RoutingAudit,
        FailoverRule,
        FailoverEvent,
    ]
    for model in models:
        assert model.__tablename__
        print("OK: model", model.__name__)
    return True


def verify_routes(app):
    routes = {str(rule) for rule in app.url_map.iter_rules()}
    required_api = [
        "/api/v1/federation/labs",
        "/api/v1/federation/labs/<lab_id>",
        "/api/v1/federation/labs/<lab_id>/connect",
        "/api/v1/federation/labs/<lab_id>/disconnect",
        "/api/v1/federation/providers",
        "/api/v1/federation/capacity",
        "/api/v1/federation/capacity/update",
        "/api/v1/federation/capacity/history",
        "/api/v1/federation/route",
        "/api/v1/federation/routing-decisions",
        "/api/v1/federation/routing-audit",
        "/api/v1/federation/failover/check",
        "/api/v1/federation/failover/events",
    ]
    required_web = [
        "/federation",
        "/federation/labs",
        "/federation/capacity",
        "/federation/routing",
        "/federation/failover",
    ]
    for route in required_api + required_web:
        if route in routes:
            print("OK:", route)
        else:
            print("MISSING:", route)
            return False
    return True


def verify_no_duplicate_routes(app):
    seen = set()
    for rule in app.url_map.iter_rules():
        if "/federation" not in str(rule):
            continue
        key = (str(rule.rule), tuple(sorted(rule.methods)))
        if key in seen:
            print("DUPLICATE:", key)
            return False
        seen.add(key)
    print("OK: no duplicate federation routes")
    return True


def verify_seed_and_flow():
    with app.app_context():
        db.create_all()
        summary = seed_federation_demo()
        if summary["labs_created"] < 10:
            print("MISSING: federated labs", summary["labs_created"])
            return False
        print("OK: seed demo", summary["labs_created"], "labs")

        lab = FederatedLab.query.filter_by(status="ONLINE").first()
        calc = CapacityCalculatorService.calculate_for_lab(lab.id)
        if calc["total_capacity"] <= 0:
            print("MISSING: capacity calculation")
            return False
        print("OK: capacity calculation")

        for l in FederatedLab.query.all():
            l.status = "ONLINE"
            l.connection_status = "CONNECTED"
        db.session.commit()
        route = SmartRoutingService.route(
            {"test_code": "GLU", "origin_latitude": 10.8, "origin_longitude": 106.7}
        )
        if not route["selected_lab"]["lab_id"]:
            print("MISSING: smart routing best lab")
            return False
        print("OK: smart routing", route["selected_lab"]["lab_code"], route["selected_lab"]["score_total"])

        offline = FederatedLab.query.first()
        offline.status = "OFFLINE"
        db.session.commit()
        failover = FailoverService.check({"federated_lab_id": offline.id})
        if failover["events_triggered"] < 1:
            print("MISSING: failover check")
            return False
        print("OK: failover check", failover["events_triggered"], "events")
        return True


app = create_app()
print("\n=== DXCON FEDERATION VERIFY ===\n")
errors = 0
if not verify_models_import():
    errors += 1
if not verify_routes(app):
    errors += 1
if not verify_no_duplicate_routes(app):
    errors += 1
if not verify_seed_and_flow():
    errors += 1
if errors:
    print("\nFAILED:", errors, "issue(s)")
    sys.exit(1)
print("\nFEDERATION VERIFY PASSED\n")
