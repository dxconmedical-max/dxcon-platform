"""Enterprise Analytics web rendering helpers — Phase 4 Sprint 4.6."""

from __future__ import annotations

import html
import json

from app.services import enterprise_analytics_service as svc
from app.web.demo_pilot_lib import metric_cards, page_header, pilot_styles

ANALYTICS_NAV = (
    ("Overview", "/enterprise-analytics"),
    ("Revenue", "/enterprise-analytics/revenue"),
    ("Lab SLA", "/enterprise-analytics/lab-sla"),
    ("Collectors", "/enterprise-analytics/collectors"),
    ("Partners", "/enterprise-analytics/partners"),
    ("Turnaround Time", "/enterprise-analytics/tat"),
    ("Rejections", "/enterprise-analytics/rejections"),
    ("Critical Results", "/enterprise-analytics/critical"),
    ("AI Usage", "/enterprise-analytics/ai"),
    ("Integrations", "/enterprise-analytics/integrations"),
    ("Export", "/enterprise-analytics/export"),
)


def analytics_styles() -> str:
    return pilot_styles() + """
    .feature-list { columns:2; gap:24px; font-size:13px; color:#334155; }
    pre { background:#0f172a; color:#e2e8f0; padding:12px; border-radius:8px; overflow:auto; max-width:100%; white-space:pre-wrap; }
    .muted-note { color:#64748b; font-size:13px; margin-bottom:16px; }
    """


def render_analytics_page(title: str, body_html: str) -> str:
    nav = "".join(f'<a href="{href}">{label}</a>' for label, href in ANALYTICS_NAV)
    return f"""
    <html>
    <head>
        <title>{title}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <style>{analytics_styles()}</style>
    </head>
    <body>
        <div class="wrap">
            <div class="nav">{nav}</div>
            <div class="muted-note">Read-only analytics · Phase 4 Sprint 4.6</div>
            {body_html}
        </div>
    </body>
    </html>
    """


def _table(headers: list[str], rows: list[list[str]]) -> str:
    if not rows:
        return "<p class='muted'>No records in this period.</p>"
    head = "".join(f"<th>{h}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>" for row in rows)
    return f"<table><tr>{head}</tr>{body}</table>"


def build_dashboard_body() -> str:
    data = svc.dashboard_payload()
    summary = data["summary"]
    cards = metric_cards(
        [
            ("Gross Revenue", summary["gross_revenue"]),
            ("Lab SLA %", summary["lab_sla_compliance_percent"]),
            ("Partners", summary["partners_tracked"]),
            ("Rejections", summary["rejections_total"]),
            ("Critical Items", summary["critical_items"]),
            ("AI Requests", summary["ai_requests"]),
            ("Integration DLQ", summary["integration_dead_letters"]),
        ]
    )
    features = "".join(f"<li>{item}</li>" for item in data["features"])
    return f"""
    {page_header("Enterprise Analytics", "Executive, operations, and partner performance insights.")}
    {cards}
    <div class="card" style="margin-top:20px;">
        <h3>Sprint 4.6 Features</h3>
        <ul class="feature-list">{features}</ul>
    </div>
    """


def build_revenue_body() -> str:
    data = svc.revenue_analytics()
    rows = [
        [str(item["partner_id"]), str(item["invoices_paid"]), f"{item['revenue']:.2f}"]
        for item in data.get("top_partners_by_revenue", [])[:10]
    ]
    return f"""
    {page_header("Revenue Analytics", f"Period {data['period_start']} to {data['period_end']}.")}
    {metric_cards([
        ("Gross Revenue", data.get("gross_revenue", 0)),
        ("Invoices Paid", data.get("invoices_paid", 0)),
        ("Payment Total", data.get("payment_total", 0)),
        ("Invoices Total", data.get("invoices_total", 0)),
    ])}
    <div class="card"><h3>Top Partners by Revenue</h3>{_table(["Partner", "Invoices", "Revenue"], rows)}</div>
    """


def build_lab_sla_body() -> str:
    data = svc.lab_sla_analytics()
    current = data["current_ops"]
    period = data["period_summary"]
    return f"""
    {page_header("Lab SLA Analytics", "Accession turnaround and SLA compliance.")}
    {metric_cards([
        ("Current SLA %", current["sla_compliance_percent"]),
        ("Avg TAT (min)", current["average_tat_minutes"]),
        ("Open Critical", current["critical_results_open"]),
        ("Pending Samples", current["pending_samples"]),
        ("Period SLA %", period["sla_compliance_percent"]),
        ("Period Breaches", period["sla_breaches"]),
    ])}
    """


def build_collectors_body() -> str:
    data = svc.collector_sla_analytics()
    rows = [
        [
            html.escape(str(row["collector_id"])),
            str(row["orders_assigned"]),
            str(row["orders_completed"]),
            f"{row['completion_rate']}%",
        ]
        for row in data.get("collectors", [])[:15]
    ]
    return f"""
    {page_header("Collector SLA Analytics", f"Completion rate threshold {data['sla_threshold_percent']}%.")}
    {metric_cards([
        ("Collectors", data.get("collectors_total", 0)),
        ("SLA Compliant", data.get("collectors_sla_compliant", 0)),
        ("Active Collectors", data.get("active_collectors", 0)),
    ])}
    <div class="card"><h3>Collector Productivity</h3>{_table(["Collector", "Assigned", "Completed", "Rate"], rows)}</div>
    """


def build_partners_body() -> str:
    data = svc.partner_performance()
    rows = [
        [
            html.escape(row.get("display_name") or row.get("partner_code") or ""),
            str(row.get("orders_total", 0)),
            f"{row.get('revenue', 0):.2f}",
            f"{row.get('completion_rate', 0)}%",
            f"{row.get('sla_compliance_rate', 0)}%",
        ]
        for row in data.get("partners", [])[:15]
    ]
    return f"""
    {page_header("Partner Performance", f"Platform SLA {data.get('platform_sla_compliance_rate', 0)}%.")}
    {metric_cards([("Partners", data.get("partners_total", 0))])}
    <div class="card"><h3>Partner Scorecard</h3>{_table(["Partner", "Orders", "Revenue", "Completion", "SLA"], rows)}</div>
    """


def build_tat_body() -> str:
    data = svc.turnaround_time_analytics()
    return f"""
    {page_header("Turnaround Time Analytics", "Lab result release and accession TAT.")}
    {metric_cards([
        ("Avg TAT Hours", data.get("average_tat_hours", 0)),
        ("Results Released", data.get("results_released", 0)),
        ("Accession TAT (min)", data.get("lab_accession_tat_minutes", 0)),
    ])}
    <div class="card"><h3>KPI Metrics</h3><pre>{html.escape(json.dumps(data.get("kpi_metrics", {}), indent=2))}</pre></div>
    """


def build_rejections_body() -> str:
    data = svc.sample_rejection_analytics()
    rejections = data["rejections"]
    rates = data["rejection_rates"]
    return f"""
    {page_header("Sample Rejection Analytics", "Rejected orders, samples, and lab results.")}
    {metric_cards([
        ("Total Rejections", rejections["total"]),
        ("Orders", rejections["orders"]),
        ("Samples", rejections["samples"]),
        ("Lab Results", rejections["lab_results"]),
        ("Order Rate %", rates["orders_percent"]),
        ("Sample Rate %", rates["samples_percent"]),
    ])}
    """


def build_critical_body() -> str:
    data = svc.critical_result_analytics()
    return f"""
    {page_header("Critical Result Analytics", "Critical flags and open escalation cases.")}
    {metric_cards([
        ("Critical Items", data.get("critical_items", 0)),
        ("Critical Rate %", data.get("critical_rate_percent", 0)),
        ("Open Cases", data.get("open_critical_results", 0)),
    ])}
    <div class="card"><h3>By Status</h3><pre>{html.escape(json.dumps(data.get("by_status", {}), indent=2))}</pre></div>
    """


def build_ai_body() -> str:
    data = svc.ai_usage_analytics()
    totals = data["usage"]["totals"]
    return f"""
    {page_header("AI Usage Analytics", "Interpretation and platform AI consumption.")}
    {metric_cards([
        ("Requests", totals.get("requests", 0)),
        ("Tokens In", totals.get("tokens_in", 0)),
        ("Tokens Out", totals.get("tokens_out", 0)),
        ("Interpretation Rate %", data.get("interpretation_rate_percent", 0)),
    ])}
    <div class="card"><h3>By Task Type</h3><pre>{html.escape(json.dumps(totals.get("by_task_type", {}), indent=2))}</pre></div>
    """


def build_integrations_body() -> str:
    data = svc.integration_failure_analytics()
    rows = [
        [
            html.escape(str(item.get("id", ""))),
            html.escape(str(item.get("reason", item.get("failure_reason", "")))),
            html.escape(str(item.get("created_at", ""))),
        ]
        for item in data.get("dead_letters", [])[:15]
    ]
    hub = data.get("hub_status", {})
    return f"""
    {page_header("Integration Failure Analytics", "Dead letters and integration hub health.")}
    {metric_cards([
        ("Dead Letters", data.get("dead_letter_count", 0)),
        ("Webhooks", hub.get("webhooks_active", 0)),
        ("Hub Status", hub.get("status", "UNKNOWN")),
    ])}
    <div class="card"><h3>Recent Dead Letters</h3>{_table(["ID", "Reason", "Created"], rows)}</div>
    """


def build_export_body() -> str:
    export_json = svc.executive_kpi_export()
    export_csv = svc.executive_kpi_export(export_format="csv")
    return f"""
    {page_header("Executive KPI Export", "Download-ready executive bundle (read-only).")}
    <div class="card">
        <p>API endpoints:</p>
        <ul>
            <li><code>GET /api/v1/enterprise-analytics/export</code></li>
            <li><code>GET /api/v1/enterprise-analytics/export?format=csv</code></li>
        </ul>
    </div>
    <div class="card"><h3>JSON Preview</h3><pre>{html.escape(json.dumps(export_json, indent=2, default=str)[:6000])}</pre></div>
    <div class="card"><h3>CSV Preview</h3><pre>{html.escape(export_csv.get("csv", ""))}</pre></div>
    """
