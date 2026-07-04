"""Healthcare Standards Advanced web rendering helpers."""

from __future__ import annotations

import json

from flask import session

from app.services import standards_advanced_service as svc
from app.web.demo_pilot_lib import metric_cards, page_header, pilot_styles

STANDARDS_NAV = (
    ("Dashboard", "/standards-advanced"),
    ("HL7 ORU Export", "/standards-advanced/hl7-oru"),
    ("HL7 ORM Import", "/standards-advanced/hl7-orm"),
    ("HL7 ADT Import", "/standards-advanced/hl7-adt"),
    ("FHIR Patient", "/standards-advanced/fhir-patient"),
    ("FHIR DiagnosticReport", "/standards-advanced/fhir-diagnostic"),
    ("FHIR Observation", "/standards-advanced/fhir-observation"),
    ("LOINC Validation", "/standards-advanced/loinc"),
    ("ICD-10 Validation", "/standards-advanced/icd10"),
    ("Audit Log", "/standards-advanced/audit"),
    ("Sandbox", "/standards-advanced/sandbox"),
)


def standards_styles() -> str:
    return pilot_styles() + """
    .btn { background:#0b4f6c; color:white; border:none; padding:8px 14px; border-radius:8px; cursor:pointer; font-size:13px; }
    .form-grid label { display:block; font-size:13px; color:#475569; margin-bottom:4px; }
    .form-grid input, .form-grid textarea { width:100%; max-width:520px; padding:10px; border:1px solid #cbd5e1; border-radius:8px; margin-bottom:12px; }
    .error { background:#fef2f2; border:1px solid #fecaca; color:#991b1b; padding:12px 16px; border-radius:10px; margin-bottom:16px; }
    .feature-list { columns:2; gap:24px; font-size:13px; color:#334155; }
    pre { background:#0f172a; color:#e2e8f0; padding:12px; border-radius:8px; overflow:auto; max-width:100%; white-space:pre-wrap; }
    """


def render_standards_page(title: str, body_html: str) -> str:
    nav = "".join(f'<a href="{href}">{label}</a>' for label, href in STANDARDS_NAV)
    actor = session.get("email", "Admin")
    return f"""
    <html>
    <head>
        <title>{title}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <style>{standards_styles()}</style>
    </head>
    <body>
        <div class="wrap">
            <div class="nav">{nav}</div>
            <div class="muted" style="margin-bottom:14px;">Signed in as {actor} · Phase 4 Sprint 4.4</div>
            {body_html}
        </div>
    </body>
    </html>
    """


def _table(headers: list[str], rows: list[list[str]]) -> str:
    if not rows:
        return "<p class='muted'>No records.</p>"
    head = "".join(f"<th>{h}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>" for row in rows)
    return f"<table><tr>{head}</tr>{body}</table>"


def build_dashboard_body() -> str:
    data = svc.dashboard_payload()
    summary = data["summary"]
    cards = metric_cards(
        [
            ("Code Systems", summary["code_systems"]),
            ("Mappings", summary["mappings"]),
            ("Audit Entries", summary["audit_entries"]),
            ("HL7 Types", len(summary["hl7_message_types"])),
            ("FHIR Resources", len(summary["fhir_resources"])),
        ]
    )
    features = "".join(f"<li>{item}</li>" for item in data["features"])
    return f"""
    {page_header("Healthcare Standards Advanced", "FHIR, HL7, LOINC, and ICD-10 integration foundation.")}
    {cards}
    <div class="card" style="margin-top:20px;">
        <h3>Sprint 4.4 Features</h3>
        <ul class="feature-list">{features}</ul>
    </div>
    """


def build_audit_body() -> str:
    data = svc.list_audit_log(page_size=50)
    rows = [
        [row.get("standard_type", ""), row.get("resource_type", ""), row.get("status", ""), row.get("created_at", "")]
        for row in data.get("entries", [])
    ]
    return f"""
    {page_header("Standards Audit Log", f"{data['count']} validation and mapping events.")}
    {_table(["Standard", "Resource", "Status", "Created"], rows)}
    """


def build_sandbox_body() -> str:
    data = svc.sandbox_messages()
    return f"""
    {page_header("Integration Sandbox Messages", "Sample HL7 and FHIR payloads for integration testing.")}
    <div class="card"><h3>HL7 ORU</h3><pre>{data['hl7']['oru']}</pre></div>
    <div class="card"><h3>HL7 ORM</h3><pre>{data['hl7']['orm']}</pre></div>
    <div class="card"><h3>HL7 ADT</h3><pre>{data['hl7']['adt']}</pre></div>
    <div class="card"><h3>FHIR Patient</h3><pre>{json.dumps(data['fhir']['patient'], indent=2)}</pre></div>
    """


def build_json_form(*, title: str, subtitle: str, action: str, default: str, result: dict | None = None, error: str = "") -> str:
    flash = f'<div class="error">{error}</div>' if error else ""
    result_html = f"<pre>{json.dumps(result, indent=2, default=str)}</pre>" if result else ""
    return f"""
    {flash}
    {page_header(title, subtitle)}
    <form method="POST" class="form-grid card">
        <textarea name="payload" rows="8">{default}</textarea>
        <button class="btn" type="submit">Run</button>
    </form>
    {result_html}
    """


def build_message_form(*, title: str, subtitle: str, default: str, result: dict | None = None, error: str = "") -> str:
    flash = f'<div class="error">{error}</div>' if error else ""
    result_html = f"<pre>{json.dumps(result, indent=2, default=str)}</pre>" if result else ""
    return f"""
    {flash}
    {page_header(title, subtitle)}
    <form method="POST" class="form-grid card">
        <label>HL7 Message</label>
        <textarea name="message" rows="8">{default}</textarea>
        <button class="btn" type="submit">Import</button>
    </form>
    {result_html}
    """


def build_code_form(*, title: str, subtitle: str, field_name: str, default: str, result: dict | None = None, error: str = "") -> str:
    flash = f'<div class="error">{error}</div>' if error else ""
    result_html = f"<pre>{json.dumps(result, indent=2, default=str)}</pre>" if result else ""
    return f"""
    {flash}
    {page_header(title, subtitle)}
    <form method="POST" class="form-grid card">
        <label for="{field_name}">Code</label>
        <input id="{field_name}" name="{field_name}" value="{default}" />
        <button class="btn" type="submit">Validate</button>
    </form>
    {result_html}
    """
