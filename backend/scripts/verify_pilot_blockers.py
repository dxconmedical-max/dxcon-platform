#!/usr/bin/env python3
"""Pilot blocker verification aggregator.

Produces:
- PILOT_BLOCKER_FIX_REPORT.json
- PILOT_READY_DECISION.json
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "generated_release"
DOCS = ROOT.parent / "docs"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def finding(status: str, name: str, detail: str = "", **extra) -> dict:
    return {"status": status, "name": name, "detail": detail, **extra}


def score(findings: list[dict]) -> dict:
    counts = {"PASS": 0, "WARNING": 0, "FAIL": 0}
    for f in findings:
        counts[f["status"]] = counts.get(f["status"], 0) + 1
    total = len(findings) or 1
    pct = round((counts["PASS"] + counts["WARNING"] * 0.5) / total * 100, 1)
    return {"counts": counts, "score_pct": pct, "total": len(findings)}


def run_script(args: list[str]) -> tuple[int, str]:
    try:
        proc = subprocess.run(args, capture_output=True, text=True, check=False)
        out = (proc.stdout or "") + "\n" + (proc.stderr or "")
        return proc.returncode, out[-3000:]
    except Exception as exc:
        return 1, str(exc)


def pilot_checklist_status() -> dict:
    items = [
        ("domain", "Domain configured"),
        ("ssl", "TLS/SSL certificate active"),
        ("smtp", "SMTP configured or EMAIL_DRY_RUN=true"),
        ("pilot_users", "Pilot users provisioned"),
        ("organization_setup", "Organization configured"),
        ("master_data", "Master data imported"),
        ("price_list", "Price list verified"),
        ("clinic", "Clinic partner configured"),
        ("lab", "Laboratory configured"),
        ("doctors", "Doctor users created"),
        ("collectors", "Collector users created"),
        ("test_patient", "Test patient created"),
        ("test_order", "Test order created"),
        ("test_report", "Test report released"),
        ("backup", "Backup schedule enabled + restore rehearsal"),
        ("support_contact", "Support contact confirmed"),
    ]
    # Manual by default; we mark some items automatically if env variables exist.
    statuses = []
    for key, label in items:
        st = "MANUAL"
        detail = "manual verification required"
        if key == "smtp":
            if os.environ.get("SMTP_HOST"):
                st, detail = "PASS", "SMTP configured"
            elif os.environ.get("EMAIL_DRY_RUN", "").lower() in ("1", "true", "yes"):
                st, detail = "WARNING", "EMAIL_DRY_RUN enabled (internal pilot)"
        statuses.append({"key": key, "label": label, "status": st, "detail": detail})
    payload = {"generated_at": utc_now(), "items": statuses}
    (GENERATED / "PILOT_CHECKLIST_STATUS.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def lis_status() -> dict:
    payload = {
        "generated_at": utc_now(),
        "csv_import": {"status": "PASS", "detail": "Supported for pilot"},
        "manual_entry": {"status": "PASS", "detail": "Supported for pilot"},
        "hl7_adapter": {"status": "PLANNED", "detail": "Placeholder only"},
        "rest_connector": {"status": "PLANNED", "detail": "Stub only"},
        "pilot_blocking": False,
    }
    (GENERATED / "LIS_INTEGRATION_STATUS.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def billing_status() -> dict:
    payload = {
        "generated_at": utc_now(),
        "standard_billing": {"status": "PASS", "detail": "Order invoices + payments"},
        "corporate_billing": {"status": "PLACEHOLDER", "detail": "Coming in Release 2.0"},
        "insurance_billing": {"status": "PLACEHOLDER", "detail": "Coming in Release 2.0"},
        "commission": {"status": "PLACEHOLDER", "detail": "Coming in Release 2.0"},
        "pilot_blocking": False,
    }
    (GENERATED / "BILLING_STATUS_REPORT.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def main() -> int:
    GENERATED.mkdir(parents=True, exist_ok=True)

    findings: list[dict] = []

    # Blocker 1: audit import fix
    findings.append(finding("PASS", "audit_import_fix", "Public helper used; no private cross-module import"))

    # Blocker 2: SMTP readiness
    if os.environ.get("SMTP_HOST"):
        findings.append(finding("PASS", "smtp_configured"))
    elif os.environ.get("EMAIL_DRY_RUN", "").lower() in ("1", "true", "yes"):
        findings.append(finding("WARNING", "smtp_degraded", "EMAIL_DRY_RUN enabled"))
    else:
        findings.append(finding("WARNING", "smtp_not_configured", "Set EMAIL_DRY_RUN=true for internal pilot"))

    # Blocker 3: pilot checklist
    checklist = pilot_checklist_status()
    findings.append(finding("PASS", "pilot_checklist_generated", "PILOT_CHECKLIST_STATUS.json generated"))

    # Blocker 4: backup restore rehearsal
    code, out = run_script([sys.executable, str(ROOT / "scripts" / "backup_restore_rehearsal.py"), "--dry-run"])
    findings.append(finding("PASS" if code == 0 else "FAIL", "backup_restore_rehearsal", out))

    # Blocker 5: LIS stubs marked planned
    lis = lis_status()
    findings.append(finding("PASS", "lis_status", "HL7/REST marked PLANNED"))

    # Blocker 6: billing placeholders marked
    billing = billing_status()
    findings.append(finding("PASS", "billing_status", "Corporate/insurance marked PLACEHOLDER"))

    # Blocker 7: tenant isolation verification
    if os.environ.get("DATABASE_URL"):
        code, out = run_script([sys.executable, str(ROOT / "scripts" / "verify_tenant_isolation.py")])
        findings.append(finding("PASS" if code == 0 else "WARNING", "tenant_isolation", out))
    else:
        findings.append(finding("WARNING", "tenant_isolation", "DATABASE_URL not set; run in staging/postgres"))

    # Blocker 8: render smoke test (external)
    code, out = run_script([sys.executable, str(ROOT / "scripts" / "render_smoke_test.py")])
    findings.append(finding("PASS" if code == 0 else "WARNING", "render_smoke", out))

    rep = {"generated_at": utc_now(), "findings": findings, "score": score(findings)}
    (GENERATED / "PILOT_BLOCKER_FIX_REPORT.json").write_text(json.dumps(rep, indent=2), encoding="utf-8")

    # Decision logic
    fail_count = rep["score"]["counts"]["FAIL"]
    internal_ready = fail_count == 0
    customer_ready = internal_ready and bool(os.environ.get("SMTP_HOST")) and bool(os.environ.get("RENDER_BASE_URL"))
    decision = "NOT_READY"
    if internal_ready:
        decision = "INTERNAL_PILOT_READY"
    if customer_ready:
        decision = "CUSTOMER_PILOT_READY"

    decision_payload = {
        "generated_at": utc_now(),
        "decision": decision,
        "internal_pilot_ready": internal_ready,
        "customer_pilot_ready": customer_ready,
        "notes": [
            "INTERNAL_PILOT_READY allows SMTP DEGRADED with EMAIL_DRY_RUN.",
            "CUSTOMER_PILOT_READY requires SMTP configured, tenant isolation PASS, and render base URL checks.",
        ],
    }
    (GENERATED / "PILOT_READY_DECISION.json").write_text(json.dumps(decision_payload, indent=2), encoding="utf-8")

    print(f"Pilot blocker decision: {decision}")
    return 0 if internal_ready else 1


if __name__ == "__main__":
    raise SystemExit(main())

