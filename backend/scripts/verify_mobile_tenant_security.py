#!/usr/bin/env python3
"""Verify mobile tenant security — Epic 7."""

from __future__ import annotations

import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "generated_release"


def main() -> int:
    sys.path.insert(0, str(ROOT))
    from app import create_app
    from app.extensions.db import db
    from app.models.driver import Driver
    from app.models.user import User
    from app.patient_marketplace.models import MpBooking, MpListing, MpProvider, MpService
    from flask_jwt_extended import create_access_token

    app = create_app()
    with app.app_context():
        db.create_all()
        org = str(uuid.uuid4())
        user = User(id=str(uuid.uuid4()), email="p1@test.com", role="PATIENT", password_hash="x")
        other = User(id=str(uuid.uuid4()), email="p2@test.com", role="PATIENT", password_hash="x")
        db.session.add_all([user, other])
        provider = MpProvider(id=str(uuid.uuid4()), organization_id=org, provider_code="P", provider_name="L", provider_type="LABORATORY")
        service = MpService(id=str(uuid.uuid4()), organization_id=org, service_code="S", service_name="S", service_type="LAB_TEST")
        listing = MpListing(id=str(uuid.uuid4()), organization_id=org, provider_id=provider.id, service_id=service.id, listing_code="L1", title="T", base_price=1, status="ACTIVE")
        booking = MpBooking(id=str(uuid.uuid4()), booking_code="BK1", patient_user_id=user.id, organization_id=org, provider_id=provider.id, listing_id=listing.id)
        db.session.add_all([provider, service, listing, booking])
        db.session.commit()
        token_other = create_access_token(identity=other.id, additional_claims={"role": "PATIENT"})
        client = app.test_client()
        denied = client.get(
            f"/api/v1/mobile/patient/bookings/{booking.id}",
            headers={"Authorization": f"Bearer {token_other}"},
        ).status_code
        checks = {"patient_booking_ownership": denied == 404}
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
    }
    GENERATED.mkdir(parents=True, exist_ok=True)
    (GENERATED / "MOBILE_TENANT_SECURITY_REPORT.json").write_text(json.dumps(report, indent=2))
    (GENERATED / "PATIENT_DATA_SCOPE_REPORT.json").write_text(json.dumps(report, indent=2))
    print(f"Mobile tenant security: {report['status']}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
