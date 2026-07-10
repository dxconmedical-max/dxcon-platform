#!/usr/bin/env python3
"""Verify webhook engine — Epic 3.5."""
import json, os, sys
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
GENERATED = ROOT / "generated_release"

def main():
    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    from app import create_app
    from app.extensions.db import db
    from app.integration.webhooks.engine import create_subscription, queue_delivery, sign_webhook_payload, simulate_delivery
    from app.partner_foundation.service import ensure_default_organization
    app = create_app()
    with app.app_context():
        db.create_all()
        org = ensure_default_organization().id
        sub = create_subscription({"event_type": "order.created", "endpoint_url": "https://hooks.example.com/dxcon"}, organization_id=org, actor="v")
        sig = sign_webhook_payload("secret", b"{}", 1700000000)
        dlv = queue_delivery(sub["id"], "order.created", {"id": "1"}, organization_id=org)
        result = simulate_delivery(dlv["delivery_id"], success=True)
        db.session.commit()
        ok = result["status"] == "DELIVERED" and len(sig) == 64
    report = {"status": "PASS" if ok else "FAIL", "webhook_signing": bool(sig), "generated_at": datetime.now(timezone.utc).isoformat()}
    GENERATED.mkdir(parents=True, exist_ok=True)
    (GENERATED / "WEBHOOK_ENGINE_REPORT.json").write_text(json.dumps(report, indent=2))
    print(report["status"])
    return 0 if ok else 1
if __name__ == "__main__":
    raise SystemExit(main())
