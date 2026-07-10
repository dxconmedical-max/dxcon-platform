#!/usr/bin/env python3
"""Verify integration security — Epic 3.5."""
import json, sys
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
GENERATED = ROOT / "generated_release"

def main():
    from app.integration.security import validate_endpoint_url, mask_payload_preview
    ok_https, _ = validate_endpoint_url("https://api.partner.example.com/hook", production=True)
    blocked, _ = validate_endpoint_url("http://127.0.0.1/hook", production=True)
    masked = mask_payload_preview('{"password":"secret","patient_code":"P1"}')
    ok = ok_https and not blocked and "***" in masked
    report = {"status": "PASS" if ok else "FAIL", "ssrf_blocked": not blocked, "masking": "***" in masked, "generated_at": datetime.now(timezone.utc).isoformat()}
    GENERATED.mkdir(parents=True, exist_ok=True)
    (GENERATED / "INTEGRATION_SECURITY_REPORT.json").write_text(json.dumps(report, indent=2))
    print(report["status"])
    return 0 if ok else 1
if __name__ == "__main__":
    raise SystemExit(main())
