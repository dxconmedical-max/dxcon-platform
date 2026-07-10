#!/usr/bin/env python3
"""Verify Patient Marketplace — Epic 5."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "generated_release"
sys.path.insert(0, str(ROOT))


def main() -> int:
    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    from app import create_app
    from app.extensions.db import db
    from app.patient_marketplace.models import MpListing, MpProvider, MpService
    from app.patient_marketplace.service import SearchService
    from app.partner_foundation.service import ensure_default_organization

    app = create_app()
    checks = {}
    with app.app_context():
        db.create_all()
        org = ensure_default_organization()
        provider = MpProvider(
            organization_id=org.id, provider_code="V-MP", provider_name="Lab", provider_type="LABORATORY", public_status="ACTIVE"
        )
        service = MpService(organization_id=org.id, service_code="T1", service_name="Test", service_type="LAB_TEST")
        db.session.add_all([provider, service])
        db.session.commit()
        listing = MpListing(
            organization_id=org.id, provider_id=provider.id, service_id=service.id,
            listing_code="L1", title="Active", status="ACTIVE", base_price=100000, partner_consent=True,
        )
        db.session.add(listing)
        db.session.commit()
        checks["active_listings"] = SearchService.search_listings()["count"] >= 1
        checks["health_route"] = app.test_client().get("/api/v1/marketplace/v2/health").status_code == 200
    status = "PASS" if all(checks.values()) else "FAIL"
    report = {"generated_at": datetime.now(timezone.utc).isoformat(), "status": status, "checks": checks}
    GENERATED.mkdir(parents=True, exist_ok=True)
    (GENERATED / "MARKETPLACE_REPORT.json").write_text(json.dumps(report, indent=2))
    print(f"Marketplace: {status}")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
