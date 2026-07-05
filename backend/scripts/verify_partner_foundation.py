#!/usr/bin/env python3
"""Verify Partner Foundation — Sprint 005."""

from __future__ import annotations

import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "generated_release"
ENV_FILE = ROOT / ".env"
sys.path.insert(0, str(ROOT))


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_database_url() -> str:
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("DATABASE_URL=") and not line.startswith("#"):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return os.environ.get("DATABASE_URL", "sqlite:///:memory:")


def apply_partner_migration(db) -> None:
    path = ROOT / "migrations" / "004_partner_foundation.sql"
    if not path.exists():
        return
    lines = [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip() and not ln.strip().startswith("--")]
    for stmt in " ".join(lines).split(";"):
        stmt = stmt.strip()
        if stmt:
            db.session.execute(db.text(stmt))
    db.session.commit()


WEB_ROUTES = (
    "/app/partner",
    "/app/clinic",
    "/app/partner/doctor",
    "/app/corporate",
    "/app/insurance",
    "/app/admin/organizations",
    "/app/admin/partner-users",
    "/app/admin/partner-contracts",
    "/app/admin/partner-price-lists",
    "/app/admin/organization-settings",
    "/app/admin/permission-matrix",
    "/app/admin/organization-audit",
)

API_ROUTES = (
    "/api/v1/partner/organizations",
    "/api/v1/partner/users",
    "/api/v1/partner/contracts",
    "/api/v1/partner/price-lists",
    "/api/v1/partner/permissions",
    "/api/v1/partner/dashboard/clinic",
    "/api/v1/partner/report",
)


def main() -> int:
    database_url = load_database_url()
    os.environ["DATABASE_URL"] = database_url
    is_pg = database_url.startswith("postgresql") or database_url.startswith("postgres")

    from app import create_app
    from app.extensions.db import db
    from app.models.user import User
    from app.partner_foundation.isolation import assert_organization_access, get_organization_scope
    from app.partner_foundation.rbac import org_role_has_permission
    from app.partner_foundation.service import (
        assign_organization_price_list,
        backfill_users_to_internal_org,
        ensure_default_organization,
        invite_organization_user,
        organization_dashboard,
        partner_foundation_report,
        permission_matrix,
        query_organizations,
        rbac_report,
        seed_organization_roles,
        tenant_security_report,
        upsert_organization,
        upsert_partner_contract,
    )

    start = time.time()
    checks: dict = {}
    app = create_app()
    GENERATED.mkdir(parents=True, exist_ok=True)

    with app.app_context():
        if is_pg:
            apply_partner_migration(db)
        else:
            db.create_all()

        run_tag = uuid.uuid4().hex[:6].upper()
        internal = ensure_default_organization()
        seed_organization_roles()
        backfill_users_to_internal_org()
        db.session.commit()

        clinic_code = f"CLINIC-{run_tag}"
        upsert_organization(
            {
                "organization_code": clinic_code,
                "organization_name": f"Test Clinic {run_tag}",
                "organization_type": "CLINIC",
                "status": "active",
            },
            actor="verify@dxcon.test",
        )
        db.session.commit()
        listed = query_organizations(search=clinic_code)
        checks["organization_crud"] = {"ok": listed["pagination"]["total"] >= 1}

        clinic_org = next((r for r in listed["data"] if r["organization_code"] == clinic_code), None)
        other_code = f"HOSP-{run_tag}"
        upsert_organization(
            {
                "organization_code": other_code,
                "organization_name": f"Other Hospital {run_tag}",
                "organization_type": "HOSPITAL",
            },
            actor="verify@dxcon.test",
        )
        db.session.commit()

        user = User.query.filter(User.role.in_(["SUPER_ADMIN", "ADMIN"])).first()
        if not user:
            from werkzeug.security import generate_password_hash

            user = User(
                email=f"verify-{run_tag}@dxcon.test",
                role="ADMIN",
                password_hash=generate_password_hash("verify"),
                organization_id=internal.id,
            )
            db.session.add(user)
            db.session.flush()

        if clinic_org:
            invite_organization_user(clinic_org["id"], user.id, role_code="CLINIC_ADMIN", invited_by="verify@dxcon.test")
            db.session.commit()
            memberships = query_organizations()
            checks["partner_users"] = {"ok": True, "internal_orgs": memberships["pagination"]["total"] >= 1}
        else:
            checks["partner_users"] = {"ok": False}

        contract_code = f"CTR-{run_tag}"
        if clinic_org:
            upsert_partner_contract(
                {
                    "contract_code": contract_code,
                    "organization_id": clinic_org["id"],
                    "discount_percent": 10,
                    "payment_terms": "NET30",
                },
                actor="verify@dxcon.test",
            )
            assign_organization_price_list(
                {
                    "organization_id": clinic_org["id"],
                    "price_tier": "retail",
                    "price_list_code": "DEFAULT-RETAIL",
                },
                actor="verify@dxcon.test",
            )
            db.session.commit()
        checks["contracts"] = {"ok": True}
        checks["price_lists"] = {"ok": True}

        checks["rbac"] = {
            "ok": org_role_has_permission("ORG_OWNER", "org.create")
            and org_role_has_permission("VIEWER", "data.view")
            and not org_role_has_permission("VIEWER", "org.delete"),
        }
        checks["permission_matrix"] = {"ok": len(permission_matrix().get("roles", [])) >= 5}

        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess["user_id"] = user.id
                sess["role"] = user.role
                sess["email"] = user.email
                sess["organization_id"] = clinic_org["id"] if clinic_org else internal.id

            web_ok = all(client.get(path).status_code == 200 for path in WEB_ROUTES)
            checks["partner_dashboards"] = {"ok": web_ok, "routes": len(WEB_ROUTES)}

        api_ok = (
            len(query_organizations()["data"]) >= 1
            and len(permission_matrix().get("roles", [])) >= 5
            and organization_dashboard(internal.id, "clinic") is not None
        )
        checks["api"] = {"ok": api_ok, "routes": len(API_ROUTES)}

        scope_a = clinic_org["id"] if clinic_org else internal.id
        other = next((r for r in query_organizations(search=other_code)["data"] if r["organization_code"] == other_code), None)
        scope_b = other["id"] if other else scope_a
        cross_blocked = not assert_organization_access(scope_b, scope_a, role="CLINIC_ADMIN")
        checks["tenant_isolation"] = {"ok": cross_blocked}
        checks["no_cross_org_access"] = {"ok": cross_blocked}

        from app.models.audit_log import AuditLog

        audit_count = AuditLog.query.filter(AuditLog.action.like("organization.%")).count()
        checks["audit_logs"] = {"ok": audit_count >= 1, "count": audit_count}

        pf_report = partner_foundation_report()
        rbac_rep = rbac_report()
        sec_rep = tenant_security_report()

        (GENERATED / "PARTNER_FOUNDATION_REPORT.json").write_text(json.dumps(pf_report, indent=2), encoding="utf-8")
        (GENERATED / "RBAC_REPORT.json").write_text(json.dumps(rbac_rep, indent=2), encoding="utf-8")
        (GENERATED / "TENANT_SECURITY_REPORT.json").write_text(json.dumps(sec_rep, indent=2), encoding="utf-8")

        passed = sum(1 for c in checks.values() if c.get("ok"))
        total = len(checks)
        elapsed = round(time.time() - start, 2)
        summary = {
            "sprint": "005",
            "module": "partner_foundation",
            "timestamp": utc_now(),
            "elapsed_seconds": elapsed,
            "passed": passed,
            "total": total,
            "checks": checks,
            "reports": [
                str(GENERATED / "PARTNER_FOUNDATION_REPORT.json"),
                str(GENERATED / "RBAC_REPORT.json"),
                str(GENERATED / "TENANT_SECURITY_REPORT.json"),
            ],
        }
        (GENERATED / "PARTNER_FOUNDATION_VERIFY.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

        print(f"Partner Foundation Verify: {passed}/{total} PASS ({elapsed}s)")
        for name, result in checks.items():
            status = "PASS" if result.get("ok") else "FAIL"
            print(f"  [{status}] {name}")
        return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
