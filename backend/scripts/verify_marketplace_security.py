#!/usr/bin/env python3
"""Verify marketplace security — Epic 5."""

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
    from app.patient_marketplace.models import MpProvider
    from app.patient_marketplace.service import MarketplaceError, SearchService
    from app.partner_foundation.service import ensure_default_organization

    app = create_app()
    checks = {}
    with app.app_context():
        db.create_all()
        org = ensure_default_organization()
        hidden = MpProvider(
            organization_id=org.id, provider_code="H1", provider_name="Hidden", provider_type="LABORATORY", public_status="INACTIVE"
        )
        db.session.add(hidden)
        db.session.commit()
        try:
            SearchService.provider_profile(hidden.id)
            checks["hidden_provider_blocked"] = False
        except MarketplaceError:
            checks["hidden_provider_blocked"] = True
        checks["org_header_required"] = app.test_client().post("/api/v1/marketplace/v2/bookings", json={}).status_code == 400
    status = "PASS" if all(checks.values()) else "FAIL"
    report = {"status": status, "checks": checks, "generated_at": datetime.now(timezone.utc).isoformat()}
    (ROOT / "generated_release" / "MARKETPLACE_SECURITY_REPORT.json").write_text(json.dumps(report, indent=2))
    print(f"Marketplace security: {status}")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
