#!/usr/bin/env python3
"""Verify pricing engine — Epic 5."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> int:
    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    from app import create_app
    from app.extensions.db import db
    from app.patient_marketplace.models import MpListing, MpProvider, MpService
    from app.patient_marketplace.service import PricingService
    from app.partner_foundation.service import ensure_default_organization

    app = create_app()
    with app.app_context():
        db.create_all()
        org = ensure_default_organization()
        p = MpProvider(organization_id=org.id, provider_code="P1", provider_name="L", provider_type="LABORATORY", public_status="ACTIVE")
        s = MpService(organization_id=org.id, service_code="S1", service_name="T", service_type="LAB_TEST")
        db.session.add_all([p, s])
        db.session.commit()
        l = MpListing(organization_id=org.id, provider_id=p.id, service_id=s.id, listing_code="PL1", title="T", status="ACTIVE", base_price=100000, partner_consent=True, home_collection_available=True)
        db.session.add(l)
        db.session.commit()
        q = PricingService.quote(l.id, distance_km=3)
        ok = "pricing_snapshot_id" in q and q["total_amount"] > 100000
    report = {"status": "PASS" if ok else "FAIL", "pricing_snapshot": ok, "generated_at": datetime.now(timezone.utc).isoformat()}
    (ROOT / "generated_release" / "PRICING_ENGINE_REPORT.json").write_text(json.dumps(report, indent=2))
    print(f"Pricing engine: {report['status']}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
