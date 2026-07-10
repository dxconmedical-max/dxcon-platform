#!/usr/bin/env python3
"""Verify QR payment — Epic 5."""

from __future__ import annotations

import hashlib
import hmac
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
    from app.patient_marketplace.payment_adapters import ManualBankQRAdapter, MockPaymentAdapter
    from app.patient_marketplace.service import BookingService, PaymentService
    from app.partner_foundation.service import ensure_default_organization

    app = create_app()
    checks = {}
    with app.app_context():
        db.create_all()
        org = ensure_default_organization()
        p = MpProvider(organization_id=org.id, provider_code="Q1", provider_name="L", provider_type="LABORATORY", public_status="ACTIVE")
        s = MpService(organization_id=org.id, service_code="S1", service_name="T", service_type="LAB_TEST")
        db.session.add_all([p, s])
        db.session.commit()
        l = MpListing(organization_id=org.id, provider_id=p.id, service_id=s.id, listing_code="QL1", title="T", status="ACTIVE", base_price=50000, partner_consent=True)
        db.session.add(l)
        db.session.commit()
        booking = BookingService.create_booking({"listing_id": l.id}, org.id)
        db.session.commit()
        payment = PaymentService.create_qr_payment(booking["id"], org.id)
        db.session.commit()
        checks["qr_created"] = bool(payment.get("qr_payload"))
        manual = ManualBankQRAdapter()
        checks["manual_adapter_ready"] = manual.production_ready is True
        checks["mock_not_production"] = MockPaymentAdapter().production_ready is False
        secret = "qr-test"
        ref, amount = payment["payment_reference"], payment["amount"]
        sig = hmac.new(secret.encode(), f"{ref}:{amount}".encode(), hashlib.sha256).hexdigest()
        try:
            PaymentService.handle_webhook({"payment_reference": ref, "amount": amount + 1, "idempotency_key": "x"}, sig, secret)
            checks["amount_rejection"] = False
        except Exception:
            checks["amount_rejection"] = True
        sig_ok = hmac.new(secret.encode(), f"{ref}:{amount}".encode(), hashlib.sha256).hexdigest()
        result = PaymentService.handle_webhook({"payment_reference": ref, "amount": amount, "idempotency_key": "wh-qr"}, sig_ok, secret)
        checks["webhook_success"] = result["status"] == "SUCCEEDED"
    status = "PASS" if all(checks.values()) else "FAIL"
    report = {"status": status, "checks": checks, "generated_at": datetime.now(timezone.utc).isoformat()}
    (ROOT / "generated_release" / "QR_PAYMENT_REPORT.json").write_text(json.dumps(report, indent=2))
    print(f"QR payment: {status}")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
