"""AI Clinical Platform web rendering helpers."""

from __future__ import annotations

import json

from flask import session

from app.ai_platform.safety import CLINICAL_DISCLAIMER
from app.services import ai_clinical_service as svc
from app.web.demo_pilot_lib import metric_cards, page_header, pilot_styles

CLINICAL_NAV = (
    ("Dashboard", "/ai-clinical"),
    ("Providers", "/ai-clinical/providers"),
    ("Prompts", "/ai-clinical/prompts"),
    ("Model Router", "/ai-clinical/router"),
    ("Interpret", "/ai-clinical/interpret"),
    ("Critical Values", "/ai-clinical/critical"),
    ("Delta Check", "/ai-clinical/delta"),
    ("Reference Ranges", "/ai-clinical/reference-ranges"),
    ("Clinical Summary", "/ai-clinical/summary"),
    ("Patient Friendly", "/ai-clinical/patient-friendly"),
    ("Review Flags", "/ai-clinical/review-flags"),
    ("Audit Log", "/ai-clinical/audit"),
    ("Usage Metrics", "/ai-clinical/usage"),
    ("Safety & PHI", "/ai-clinical/safety"),
)


def clinical_styles() -> str:
    return pilot_styles() + """
    .btn { background:#4338ca; color:white; border:none; padding:8px 14px; border-radius:8px; cursor:pointer; text-decoration:none; font-size:13px; }
    .form-grid label { display:block; font-size:13px; color:#475569; margin-bottom:4px; }
    .form-grid input, .form-grid select, .form-grid textarea { width:100%; max-width:520px; padding:10px; border:1px solid #cbd5e1; border-radius:8px; margin-bottom:12px; }
    .flash { background:#ecfdf5; border:1px solid #86efac; color:#166534; padding:12px 16px; border-radius:10px; margin-bottom:16px; }
    .error { background:#fef2f2; border:1px solid #fecaca; color:#991b1b; padding:12px 16px; border-radius:10px; margin-bottom:16px; }
    .policy { background:#eef2ff; border:1px solid #c7d2fe; padding:12px 16px; border-radius:10px; margin-bottom:16px; font-size:13px; }
    .feature-list { columns:2; gap:24px; font-size:13px; color:#334155; }
    pre { background:#0f172a; color:#e2e8f0; padding:12px; border-radius:8px; overflow:auto; max-width:100%; }
    """


def render_clinical_page(title: str, body_html: str) -> str:
    nav = "".join(f'<a href="{href}">{label}</a>' for label, href in CLINICAL_NAV)
    actor = session.get("email", "Clinician")
    return f"""
    <html>
    <head>
        <title>{title}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <style>{clinical_styles()}</style>
    </head>
    <body>
        <div class="wrap">
            <div class="nav">{nav}</div>
            <div class="muted" style="margin-bottom:14px;">Signed in as {actor} · Phase 4 Sprint 4.2 · Advisory only</div>
            <div class="policy">{CLINICAL_DISCLAIMER}</div>
            {body_html}
        </div>
    </body>
    </html>
    """


def _table(headers: list[str], rows: list[list[str]]) -> str:
    if not rows:
        return "<p class='muted'>No records.</p>"
    head = "".join(f"<th>{h}</th>" for h in headers)
    body = ""
    for row in rows:
        body += "<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>"
    return f"<table><tr>{head}</tr>{body}</table>"


def build_dashboard_body() -> str:
    data = svc.dashboard_payload()
    summary = data["summary"]
    cards = metric_cards(
        [
            ("Providers", summary["providers"]),
            ("Prompts", summary["prompts"]),
            ("Audit Entries", summary["audit_entries"]),
            ("Usage Records", summary["usage_records"]),
            ("Router Tasks", summary["router_tasks"]),
        ]
    )
    features = "".join(f"<li>{item}</li>" for item in data["features"])
    return f"""
    {page_header("AI Clinical Platform", "Advisory AI layer for lab result interpretation with mandatory human review.")}
    {cards}
    <div class="card" style="margin-top:20px;">
        <h3>Sprint 4.2 Features</h3>
        <ul class="feature-list">{features}</ul>
    </div>
    """


def build_providers_body() -> str:
    data = svc.list_providers()
    rows = [
        [row.get("provider_code", ""), row.get("name", ""), row.get("provider_type", ""), row.get("status", "")]
        for row in data.get("providers", [])
    ]
    return f"""
    {page_header("AI Provider Registry", f"{data['count']} registered providers.")}
    {_table(["Code", "Name", "Type", "Status"], rows)}
    """


def build_prompts_body() -> str:
    data = svc.list_prompts()
    rows = [
        [row.get("prompt_code", ""), row.get("name", ""), row.get("task_type", ""), str(row.get("active_version", ""))]
        for row in data.get("prompts", [])
    ]
    return f"""
    {page_header("Prompt Registry", f"{data['count']} prompt templates.")}
    {_table(["Code", "Name", "Task", "Version"], rows)}
    """


def build_router_body() -> str:
    data = svc.model_router_payload()
    rows = [[task, info.get("provider_type", ""), info.get("provider_label", "")]
            for task, info in data.get("routes", {}).items()]
    return f"""
    {page_header("Model Router", "Task-to-provider routing for advisory inference.")}
    {_table(["Task Type", "Provider Type", "Provider"], rows)}
    """


def build_audit_body() -> str:
    data = svc.list_audit(page_size=50)
    rows = [
        [row.get("action", ""), row.get("resource_type", ""), row.get("actor", ""), row.get("created_at", "")]
        for row in data.get("entries", [])
    ]
    return f"""
    {page_header("AI Audit Log", f"{data['count']} audit entries.")}
    {_table(["Action", "Resource", "Actor", "Created"], rows)}
    """


def build_usage_body() -> str:
    data = svc.usage_metrics()
    totals = data.get("totals", {})
    return f"""
    {page_header("AI Usage Metrics", f"{data['count']} usage records.")}
    <div class="card">
        <p><strong>Requests:</strong> {totals.get('requests', 0)}</p>
        <p><strong>Tokens In:</strong> {totals.get('tokens_in', 0)}</p>
        <p><strong>Tokens Out:</strong> {totals.get('tokens_out', 0)}</p>
    </div>
    """


def build_review_flags_body() -> str:
    data = svc.doctor_review_flag({"pending_results": True})
    return f"""
    {page_header("Doctor Review Flag", "All AI outputs require physician review.")}
    <div class="card">
        <p><strong>Doctor Review Required:</strong> {data.get('doctor_review_required')}</p>
        <p><strong>Human Review Required:</strong> {data.get('human_review_required')}</p>
        <p><strong>Review Status:</strong> {data.get('review_status')}</p>
        <p><strong>Automatic Diagnosis:</strong> {data.get('automatic_diagnosis')}</p>
    </div>
    """


def build_safety_body(*, result: dict | None = None, error: str = "") -> str:
    flash = f'<div class="error">{error}</div>' if error else ""
    result_html = ""
    if result:
        result_html = f"<h3>Redaction Result</h3><pre>{json.dumps(result, indent=2, default=str)}</pre>"
    return f"""
    {flash}
    {page_header("Safety Disclaimer & PHI Redaction", "Every AI output is advisory and audited.")}
    <form method="POST" class="form-grid card">
        <label for="sample_text">Sample Text Containing PHI</label>
        <textarea id="sample_text" name="sample_text" rows="4">Contact patient@example.com MRN: ABC12345 phone 555-123-4567</textarea>
        <button class="btn" type="submit">Run PHI Redaction</button>
    </form>
    {result_html}
    """


def build_interpret_form_body(*, result: dict | None = None, error: str = "") -> str:
    return _analysis_form(
        title="Result Interpretation",
        subtitle="Advisory interpretation — not a diagnosis.",
        action="/ai-clinical/interpret",
        default_payload='{"items":[{"test_code":"GLU","test_name":"Glucose","result_value":"145","reference_range":"70-110","unit":"mg/dL"}]}',
        result=result,
        error=error,
    )


def build_critical_form_body(*, result: dict | None = None, error: str = "") -> str:
    return _analysis_form(
        title="Critical Value Detection",
        subtitle="Detect panic and delta alerts for physician review.",
        action="/ai-clinical/critical",
        default_payload='{"patient_id":"P-001","items":[{"test_code":"K","test_name":"Potassium","result_value":"6.8","reference_range":"3.5-5.1","flag":"CRITICAL"}]}',
        result=result,
        error=error,
    )


def build_delta_form_body(*, result: dict | None = None, error: str = "") -> str:
    return _analysis_form(
        title="Delta Check",
        subtitle="Evaluate significant change between consecutive results.",
        action="/ai-clinical/delta",
        default_payload='{"patient_id":"P-001","test_code":"CREA","current_value":"1.9","previous_value":"1.2","threshold_percent":20}',
        result=result,
        error=error,
    )


def build_reference_form_body(*, result: dict | None = None, error: str = "") -> str:
    return _analysis_form(
        title="Reference Range Explanation",
        subtitle="Explain how a result compares to reference range.",
        action="/ai-clinical/reference-ranges",
        default_payload='{"test_code":"GLU","result_value":"145","age":45,"sex":"M"}',
        result=result,
        error=error,
    )


def build_summary_form_body(*, result: dict | None = None, error: str = "") -> str:
    return _analysis_form(
        title="Clinical Summary",
        subtitle="Advisory panel summary requiring doctor review.",
        action="/ai-clinical/summary",
        default_payload='{"items":[{"test_code":"HBA1C","test_name":"HbA1c","result_value":"7.2","reference_range":"4.0-5.6","unit":"%"}]}',
        result=result,
        error=error,
    )


def build_patient_friendly_form_body(*, result: dict | None = None, error: str = "") -> str:
    return _analysis_form(
        title="Patient-Friendly Explanation",
        subtitle="Plain-language education — not a diagnosis.",
        action="/ai-clinical/patient-friendly",
        default_payload='{"items":[{"test_code":"GLU","test_name":"Glucose","result_value":"145","reference_range":"70-110","unit":"mg/dL"}]}',
        result=result,
        error=error,
    )


def _analysis_form(*, title: str, subtitle: str, action: str, default_payload: str, result: dict | None, error: str) -> str:
    flash = f'<div class="error">{error}</div>' if error else ""
    result_html = ""
    if result:
        result_html = f"<h3>Advisory Output</h3><pre>{json.dumps(result, indent=2, default=str)}</pre>"
    return f"""
    {flash}
    {page_header(title, subtitle)}
    <form method="POST" class="form-grid card">
        <label for="payload">Request JSON</label>
        <textarea id="payload" name="payload" rows="8">{default_payload}</textarea>
        <button class="btn" type="submit">Run Advisory Analysis</button>
    </form>
    {result_html}
    """
