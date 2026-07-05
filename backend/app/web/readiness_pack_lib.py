"""Readiness Pack web rendering helpers — Phase 5 Sprint 5.14."""

from __future__ import annotations

import html

from app.services import readiness_pack_service as svc
from app.web.demo_pilot_lib import metric_cards, page_header, pilot_styles, status_class

PACK_NAV = (
    ("Overview", "/readiness-pack"),
    ("System", "/readiness-pack/system"),
    ("Security", "/readiness-pack/security"),
    ("Pilot", "/readiness-pack/pilot"),
    ("Go-Live Checklist", "/readiness-pack/go-live-checklist"),
    ("Limitations", "/readiness-pack/limitations"),
    ("Roadmap v2", "/readiness-pack/roadmap"),
)


def pack_styles() -> str:
    return pilot_styles() + """
    pre.doc { background:#0f172a; color:#e2e8f0; padding:16px; border-radius:8px; overflow:auto; white-space:pre-wrap; font-size:13px; line-height:1.6; max-height:70vh; }
    .muted-note { color:#64748b; font-size:13px; margin-bottom:16px; }
    .flow { background:#0f172a; color:#e2e8f0; padding:16px; border-radius:8px; font-family:monospace; line-height:1.6; text-align:center; margin-bottom:16px; font-size:13px; }
    .checklist li { margin-bottom:10px; }
    """


def render_pack_page(title: str, body_html: str) -> str:
    nav = "".join(f'<a href="{href}">{label}</a>' for label, href in PACK_NAV)
    return f"""
    <html>
    <head>
        <title>{title}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <style>{pack_styles()}</style>
    </head>
    <body>
        <div class="wrap">
            <div class="nav">{nav}</div>
            <div class="muted-note">Go-live readiness artifacts · Phase 5 Sprint 5.14</div>
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


def _doc_body(data: dict) -> str:
    sections = "".join(f"<li>{html.escape(section)}</li>" for section in data.get("sections", []))
    content = html.escape(data.get("content", ""))
    return f"""
    {page_header(data.get("filename", data.get("report", "")), data.get("path", ""))}
    <div class="card"><h3>Sections</h3><ul>{sections or "<li class='muted'>No sections parsed.</li>"}</ul></div>
    <div class="card"><h3>Content</h3><pre class="doc">{content or "Document not found."}</pre></div>
    """


def build_dashboard_body() -> str:
    data = svc.dashboard_payload()
    summary = data["summary"]
    cards = metric_cards(
        [
            ("System Score", summary["system_score"]),
            ("Security Score", summary.get("security_score") or "—"),
            ("Pilot Score", summary.get("pilot_score") or "—"),
            ("Checklist Left", summary["checklist_remaining"]),
            ("Artifacts", f"{summary['artifacts_present']}/{summary['artifacts_total']}"),
        ]
    )
    features = "".join(f"<li>{html.escape(item)}</li>" for item in data["features"])
    links = "".join(
        f'<li>{html.escape(item["filename"])} — {"OK" if item["exists"] else "MISSING"}</li>'
        for item in data.get("inventory", [])
    )
    flow = """
    SYSTEM_READINESS → SECURITY → PILOT → GO_LIVE_CHECKLIST → LIMITATIONS → ROADMAP_v2
    """
    return f"""
    {page_header("Readiness Pack", "System, security, pilot, and go-live readiness artifacts.")}
    <div class="flow">{flow}</div>
    {cards}
    <div class="card"><h3>Sprint 5.14 Artifacts</h3><ul>{features}</ul></div>
    <div class="card"><h3>Inventory</h3><ul>{links}</ul></div>
    """


def build_system_body() -> str:
    data = svc.system_readiness_report()
    summary = data["summary"]
    rows = [
        [html.escape(name), html.escape(str(info.get("status", ""))), "Yes" if info.get("ok") else "No"]
        for name, info in data.get("checks", {}).items()
    ]
    return f"""
    {page_header("System Readiness", f"Score: {summary['score']}%")}
    {metric_cards([
        ("Score", summary["score"]),
        ("Checks", f"{summary['checks_passed']}/{summary['checks_total']}"),
        ("System", summary["system_status"]),
        ("Database", summary["database"]),
    ])}
    <div class="card"><h3>Checks</h3>{_table(["Check", "Status", "OK"], rows)}</div>
    """


def build_security_body() -> str:
    data = svc.security_readiness_report()
    summary = data.get("summary", {})
    return f"""
    {page_header("Security Readiness", data["filename"])}
    {metric_cards([
        ("Available", "Yes" if data["exists"] else "No"),
        ("Score", summary.get("score", "—")),
        ("Checks", f"{summary.get('checks_passed', '—')}/{summary.get('checks_total', '—')}"),
    ])}
    <div class="card links"><a href="/security-compliance">Security Hub</a></div>
    """


def build_pilot_body() -> str:
    data = svc.pilot_readiness_report()
    summary = data.get("summary", {})
    return f"""
    {page_header("Pilot Readiness", data["filename"])}
    {metric_cards([
        ("Available", "Yes" if data["exists"] else "No"),
        ("Score", summary.get("pilot_readiness_score", "—")),
        ("Phase", summary.get("phase", "—")),
    ])}
    <div class="card links"><a href="/pilot-checklist">Pilot Checklist</a> · <a href="/pilot-status">Pilot Status</a></div>
    """


def build_go_live_checklist_body() -> str:
    data = svc.go_live_checklist_report()
    items = "".join(
        f'<li><span class="{status_class("OK" if item.get("checked") else "WARN")}">'
        f'{"[x]" if item.get("checked") else "[ ]"}</span> {html.escape(item.get("item", ""))}</li>'
        for item in data.get("items", [])
    )
    return f"""
    {page_header("Go-Live Checklist", data["filename"])}
    {metric_cards([
        ("Items", data["items_total"]),
        ("Checked", data["items_checked"]),
        ("Remaining", data["items_remaining"]),
    ])}
    <div class="card"><h3>Checklist</h3><ul class="checklist">{items or "<li class='muted'>No items.</li>"}</ul></div>
    """


def build_limitations_body() -> str:
    return _doc_body(svc.known_limitations_doc())


def build_roadmap_body() -> str:
    return _doc_body(svc.roadmap_v2_doc())
