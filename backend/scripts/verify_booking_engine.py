#!/usr/bin/env python3
"""Verify booking engine — Epic 5."""

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
    from app.patient_marketplace.service import BookingService
    from app.partner_foundation.service import ensure_default_organization

    app = create_app()
    with app.app_context():
        db.create_all()
        org = ensure_default_organization()
        p = MpProvider(organization_id=org.id, provider_code="B1", provider_name="L", provider_type="LABORATORY", public_status="ACTIVE")
        s = MpService(organization_id=org.id, service_code="S1", service_name="T", service_type="LAB_TEST")
        db.session.add_all([p, s])
        db.session.commit()
        l = MpListing(organization_id=org.id, provider_id=p.id, service_id=s.id, listing_code="BL1", title="T", status="ACTIVE", base_price=1, partner_consent=True)
        db.session.add(l)
        db.session.commit()
        b = BookingService.create_booking({"listing_id": l.id, "idempotency_key": "bk-idem"}, org.id)
        db.session.commit()
        dup = BookingService.create_booking({"listing_id": l.id, "idempotency_key": "bk-idem"}, org.id)
        ok = b["booking_code"] == dup["booking_code"]
    report = {"status": "PASS" if ok else "FAIL", "duplicate_prevention": ok, "generated_at": datetime.now(timezone.utc).isoformat()}
    (ROOT / "generated_release" / "BOOKING_ENGINE_REPORT.json").write_text(json.dumps(report, indent=2))
    print(f"Booking engine: {report['status']}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
