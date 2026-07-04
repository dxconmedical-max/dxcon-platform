"""User Guides web rendering helpers — Phase 5 Sprint 5.8."""

from __future__ import annotations

import html

from app.services import user_guides_service as svc
from app.web.demo_pilot_lib import metric_cards, page_header, pilot_styles

GUIDES_NAV = (
    ("Overview", "/user-guides"),
    ("Reception", "/user-guides/reception"),
    ("Collector", "/user-guides/collector"),
    ("Lab", "/user-guides/lab"),
    ("Doctor", "/user-guides/doctor"),
    ("Admin", "/user-guides/admin"),
    ("Video", "/user-guides/video"),
    ("FAQ", "/user-guides/faq"),
    ("Checklist", "/user-guides/checklist"),
)


def guides_styles() -> str:
    return pilot_styles() + """
    .flow { background:#0f172a; color:#e2e8f0; padding:16px; border-radius:8px; font-family:monospace; line-height:1.6; text-align:center; margin-bottom:16px; font-size:13px; }
    .muted { color:#64748b; font-size:13px; margin-bottom:16px; }
    .checklist li { margin-bottom:10px; }
    .links a { margin-right:12px; }
    """


def render_guides_page(title: str, body_html: str) -> str:
    nav = "".join(f'<a href="{href}">{label}</a>' for label, href in GUIDES_NAV)
    return f"""
    <html>
    <head>
        <title>{title}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <style>{guides_styles()}</style>
    </head>
    <body>
        <div class="wrap">
            <div class="nav">{nav}</div>
            <div class="muted">Role training and pilot walkthrough · Phase 5 Sprint 5.8</div>
            {body_html}
        </div>
    </body>
    </html>
    """


def _role_guide_body(data: dict) -> str:
    steps = "".join(f"<li>{html.escape(step)}</li>" for step in data.get("steps", []))
    routes = "".join(f'<a href="{html.escape(route)}">{html.escape(route)}</a> ' for route in data.get("routes", []))
    accounts = data.get("demo_accounts") or []
    account_rows = "".join(
        f"<li>{html.escape(acc.get('email', ''))} ({html.escape(acc.get('role', ''))})</li>"
        for acc in accounts
    ) or "<li class='muted'>See /demo-accounts for full list.</li>"
    return f"""
    {page_header(data["title"], data.get("summary", ""))}
    <div class="card links"><h3>Key Routes</h3>{routes}</div>
    <div class="card"><h3>Steps</h3><ol class="checklist">{steps}</ol></div>
    <div class="card"><h3>Demo Accounts</h3><ul>{account_rows}</ul></div>
    """


def build_dashboard_body() -> str:
    data = svc.dashboard_payload()
    summary = data["summary"]
    cards = metric_cards(
        [
            ("Role Guides", summary["role_guides"]),
            ("FAQ Items", summary["faq_count"]),
            ("Video Links", summary["video_count"]),
            ("Checklist Items", summary["checklist_items"]),
        ]
    )
    features = "".join(f"<li>{item}</li>" for item in data["features"])
    flow = """
    <div class="flow">
        Reception Guide · Collector Guide · Lab Guide · Doctor Guide · Admin Guide<br>
        ↓<br>
        Video Link · FAQ · Checklist
    </div>
    """
    return f"""
    {page_header("User Guides", "Training paths for every pilot role on the DxCon platform.")}
    {flow}
    <div class="card"><strong>Status:</strong> {html.escape(data['status'])}</div>
    {cards}
    <div class="card"><h3>Features</h3><ul>{features}</ul></div>
    """


def build_reception_body() -> str:
    return _role_guide_body(svc.reception_guide())


def build_collector_body() -> str:
    return _role_guide_body(svc.collector_guide())


def build_lab_body() -> str:
    return _role_guide_body(svc.lab_guide())


def build_doctor_body() -> str:
    return _role_guide_body(svc.doctor_guide())


def build_admin_body() -> str:
    return _role_guide_body(svc.admin_guide())


def build_video_body() -> str:
    data = svc.video_links()
    rows = [
        [
            html.escape(str(item.get("title", ""))),
            html.escape(str(item.get("type", ""))),
            f'<a href="{html.escape(str(item.get("url", "")))}">{html.escape(str(item.get("url", "")))}</a>',
        ]
        for item in data.get("videos", [])
    ]
    head = "".join(f"<th>{h}</th>" for h in ["Title", "Type", "Link"])
    body = "".join("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>" for row in rows)
    table = f"<table><tr>{head}</tr>{body}</table>" if rows else "<p class='muted'>No videos configured.</p>"
    return f"""
    {page_header("Video Link", "Interactive walkthroughs and documentation links for pilot training.")}
    <div class="card">{table}</div>
    """


def build_faq_body() -> str:
    data = svc.user_guides_faq()
    items = "".join(
        f"<li><strong>{html.escape(item['question'])}</strong><br><span class='muted'>{html.escape(item['answer'])}</span></li>"
        for item in data.get("items", [])
    )
    return f"""
    {page_header("FAQ", "Frequently asked questions for pilot operators.")}
    <div class="card"><ul class="checklist">{items}</ul></div>
    """


def build_checklist_body() -> str:
    data = svc.user_guides_checklist()
    items = "".join(
        f"<li>{html.escape(str(item.get('item', item.get('status', ''))))}"
        f"{' → ' + html.escape(item['route']) if item.get('route') else ''}"
        f"{' [' + html.escape(str(item.get('status', ''))) + ']' if item.get('status') and not item.get('item') else ''}"
        f"</li>"
        for item in data.get("items", [])
    )
    return f"""
    {page_header("Checklist", "Role guide review and pilot training completion checklist.")}
    <div class="card"><ol class="checklist">{items}</ol></div>
    <div class="card"><p>Legacy checklist: <a href="/pilot-checklist">/pilot-checklist</a></p></div>
    """
