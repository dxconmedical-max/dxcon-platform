import os
import random
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app import create_app
from app.core.statuses import (
    FEDERATION_LAB_CONNECTED,
    FEDERATION_LAB_ONLINE,
    FEDERATION_PROVIDER_ACTIVE,
)
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
    FederationProvider,
    FederationProviderBranch,
)
from app.models.federation_failover import FailoverEvent, FailoverRule
from app.models.federation_routing import RoutingAudit, RoutingDecision, RoutingRule
from app.services.federation_failover_service import FailoverService
from app.services.federation_routing_service import SmartRoutingService


TARGETS = {
    "labs": int(os.environ.get("FEDERATION_SEED_LABS", "20")),
    "branches": int(os.environ.get("FEDERATION_SEED_BRANCHES", "80")),
    "capabilities": int(os.environ.get("FEDERATION_SEED_CAPABILITIES", "200")),
    "capacity_days": int(os.environ.get("FEDERATION_SEED_CAPACITY_DAYS", "7")),
    "routing_decisions": int(os.environ.get("FEDERATION_SEED_ROUTING", "200")),
    "failover_events": int(os.environ.get("FEDERATION_SEED_FAILOVER", "20")),
}

TEST_CODES = ["GLU", "TSH", "HBA1C", "CBC", "CRP", "ALT", "AST", "CREA"]
CITIES = ["Hanoi", "HCMC", "Da Nang", "Can Tho", "Hai Phong"]


def seed_federation_demo():
    if not RoutingRule.query.first():
        db.session.add(
            RoutingRule(
                rule_code="RTE-DEFAULT",
                name="Default Federation Routing",
            )
        )

    providers = []
    provider_count = max(4, TARGETS["labs"] // 5)
    for idx in range(provider_count):
        provider = FederationProvider(
            provider_code=f"FPRV-{idx + 1:03d}",
            name=f"Federation Provider {idx + 1}",
            provider_type="LAB_NETWORK",
            status=FEDERATION_PROVIDER_ACTIVE,
        )
        db.session.add(provider)
        providers.append(provider)
    db.session.flush()

    labs = []
    for idx in range(TARGETS["labs"]):
        provider = providers[idx % len(providers)]
        lab = FederatedLab(
            lab_code=f"FLAB-{idx + 1:03d}",
            name=f"Federated Lab {idx + 1}",
            provider_id=provider.id,
            city=random.choice(CITIES),
            latitude=10.0 + random.random() * 12,
            longitude=105.0 + random.random() * 8,
            status=FEDERATION_LAB_ONLINE if idx % 5 else "OFFLINE",
            connection_status=FEDERATION_LAB_CONNECTED if idx % 5 else "DISCONNECTED",
            priority=random.randint(40, 90),
            sla_minutes=random.choice([120, 180, 240, 360]),
            contract_active=idx % 7 != 0,
            base_price=random.randint(80000, 350000),
            connected_at=datetime.utcnow() - timedelta(days=random.randint(1, 60)),
        )
        db.session.add(lab)
        labs.append(lab)
    db.session.flush()

    branches_created = 0
    for idx in range(TARGETS["branches"]):
        provider = providers[idx % len(providers)]
        lab = labs[idx % len(labs)]
        db.session.add(
            FederationProviderBranch(
                branch_code=f"FBR-{idx + 1:04d}",
                provider_id=provider.id,
                federated_lab_id=lab.id,
                name=f"Branch {idx + 1}",
                city=lab.city,
                status="ACTIVE",
            )
        )
        branches_created += 1

    capabilities_created = 0
    cap_idx = 0
    while capabilities_created < TARGETS["capabilities"]:
        lab = labs[cap_idx % len(labs)]
        test_code = TEST_CODES[capabilities_created % len(TEST_CODES)]
        db.session.add(
            FederationCapability(
                capability_code=f"FCAP-{capabilities_created + 1:04d}",
                federated_lab_id=lab.id,
                test_code=test_code,
                test_name=f"Test {test_code}",
                turnaround_hours=random.choice([6, 12, 24, 48]),
            )
        )
        capabilities_created += 1
        cap_idx += 1

    for lab in labs:
        db.session.add(
            CapacityRule(
                rule_code=f"CRULE-{lab.lab_code}",
                federated_lab_id=lab.id,
                max_daily_tests=random.randint(300, 800),
            )
        )
        for analyzer_idx in range(random.randint(1, 3)):
            db.session.add(
                AnalyzerCapacity(
                    analyzer_code=f"AN-{lab.lab_code}-{analyzer_idx + 1}",
                    federated_lab_id=lab.id,
                    analyzer_name=f"Analyzer {analyzer_idx + 1}",
                    hourly_throughput=random.randint(10, 40),
                    status="ONLINE" if lab.status == FEDERATION_LAB_ONLINE else "OFFLINE",
                    qc_status="PASS" if random.random() > 0.1 else "FAIL",
                )
            )

    capacity_snapshots = 0
    for day in range(TARGETS["capacity_days"]):
        snapshot_date = datetime.utcnow() - timedelta(days=day)
        for lab in labs:
            total = random.randint(300, 700)
            used = random.randint(50, total - 20)
            db.session.add(
                CapacitySnapshot(
                    snapshot_code=f"FCAP-{lab.lab_code}-D{day}",
                    federated_lab_id=lab.id,
                    snapshot_date=snapshot_date,
                    total_capacity=total,
                    used_capacity=used,
                    remaining_capacity=total - used,
                    utilization_rate=round((used / total) * 100, 2),
                )
            )
            db.session.add(
                LabWorkloadSnapshot(
                    snapshot_code=f"FWL-{lab.lab_code}-D{day}",
                    federated_lab_id=lab.id,
                    snapshot_date=snapshot_date,
                    pending_orders=random.randint(5, 40),
                    in_progress_tests=random.randint(10, 80),
                    completed_tests=random.randint(50, 200),
                    average_tat_hours=round(random.uniform(8, 36), 2),
                    qc_issue_rate=round(random.uniform(0.5, 5), 2),
                )
            )
            capacity_snapshots += 1

    online_labs = [lab for lab in labs if lab.status == FEDERATION_LAB_ONLINE]
    for idx in range(TARGETS["routing_decisions"]):
        lab = online_labs[idx % len(online_labs)] if online_labs else labs[0]
        test_code = TEST_CODES[idx % len(TEST_CODES)]
        decision = RoutingDecision(
            decision_code=f"RTE-SEED-{idx + 1:04d}",
            request_ref=f"REQ-{idx + 1:05d}",
            selected_lab_id=lab.id,
            test_code=test_code,
            score_total=round(random.uniform(0.55, 0.95), 4),
            score_breakdown_json='{"capacity": 0.15, "sla": 0.12}',
            candidate_count=random.randint(3, len(labs)),
        )
        db.session.add(decision)
        db.session.flush()
        db.session.add(
            RoutingAudit(
                audit_code=f"RAU-SEED-{idx + 1:04d}",
                routing_decision_id=decision.id,
                action="ROUTE_SELECTED",
                details_json='{"seed": true}',
            )
        )

    failover_rules = 0
    for idx, lab in enumerate(labs[: min(10, len(labs))]):
        fallback = labs[(idx + 1) % len(labs)]
        db.session.add(
            FailoverRule(
                rule_code=f"FO-RULE-{idx + 1:03d}",
                name=f"Failover for {lab.lab_code}",
                trigger_type="LAB_OFFLINE",
                target_lab_id=lab.id,
                fallback_lab_id=fallback.id,
            )
        )
        failover_rules += 1

    failover_created = 0
    offline_labs = [lab for lab in labs if lab.status != FEDERATION_LAB_ONLINE][:TARGETS["failover_events"]]
    for idx, lab in enumerate(offline_labs):
        fallback = online_labs[idx % len(online_labs)] if online_labs else labs[-1]
        db.session.add(
            FailoverEvent(
                event_code=f"FO-SEED-{idx + 1:03d}",
                trigger_type="LAB_OFFLINE",
                source_lab_id=lab.id,
                fallback_lab_id=fallback.id,
                status="TRIGGERED",
                message=f"Seed failover from {lab.lab_code}",
            )
        )
        failover_created += 1

    db.session.commit()
    return {
        "labs_created": FederatedLab.query.count(),
        "providers_created": FederationProvider.query.count(),
        "branches_created": branches_created,
        "capabilities_created": capabilities_created,
        "capacity_snapshots_created": capacity_snapshots,
        "routing_decisions_created": RoutingDecision.query.count(),
        "failover_events_created": FailoverEvent.query.count(),
        "failover_rules_created": failover_rules,
    }


def main():
    app = create_app()
    with app.app_context():
        db.create_all()
        summary = seed_federation_demo()
        print("\n=== DXCON FEDERATION DEMO SEED ===\n")
        for key, value in summary.items():
            print(f"{key}: {value}")


if __name__ == "__main__":
    main()
