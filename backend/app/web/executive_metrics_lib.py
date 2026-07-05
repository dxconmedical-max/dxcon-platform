"""Executive Metrics web rendering helpers — Phase 5 Sprint 5.9."""

from __future__ import annotations

import html
import json

from app.services import executive_metrics_service as svc
from app.web.demo_pilot_lib import metric_cards, page_header, pilot_styles

METRICS_NAV = (
    ("Overview", "/executive-metrics"),
    ("Revenue", "/executive-metrics/revenue"),
    ("TAT", "/executive-metrics/tat"),
    ("Orders", "/executive-metrics/orders"),
    ("Growth", "/executive-metrics/growth"),
    ("Lab SLA", "/executive-metrics/lab-sla"),
    ("Collector SLA", "/executive-metrics/collector-sla"),
    ("Clinic Ranking", "/executive-metrics/clinic-ranking"),
    ("Doctor Ranking", "/executive-metrics/doctor-ranking"),
    ("Revenue Forecast", "/executive-metrics/revenue-forecast"),
)


def metrics_styles() -> str:
    return pilot_styles() + """
    .feature-list { columns:2; gap:24px; font-size:13px; color:#334155; }
    pre { background:#0f172a; color:#e2e8f0; padding:12px; border-radius:8px; overflow:auto; max-width:100%; white-space:pre-wrap; }
    .muted-note { color:#64748b; font-size:13px; margin-bottom:16px; }
    """


def render_metrics_page(title: str, body_html: str) -> str:
    nav = "".join(f'<a href="{href}">{label}</a>' for label, href in METRICS_NAV)
    return f"""
    <html>
    <head>
        <title>{title}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <style>{metrics_styles()}</style>
    </head>
    <body>
        <div class="wrap">
            <div class="nav">{nav}</div>
            <div class="muted-note">Executive KPI hub · Phase 5 Sprint 5.9</div>
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
            ("Orders", summary["orders_total"]),
            ("Revenue Growth %", summary["revenue_growth_percent"]),
            ("Orders Growth %", summary["orders_growth_percent"]),
            ("Lab SLA %", summary["lab_sla_compliance_percent"]),
            ("Forecast Estimate", summary["revenue_forecast_estimate"]),
            ("Clinics Ranked", summary["clinics_ranked"]),
            ("Doctors Ranked", summary["doctors_ranked"]),
        ]
    )
    features = "".join(f"<li>{item}</li>" for item in data["features"])
    flow = """
    Revenue → TAT → Orders → Growth → Lab SLA → Collector SLA → Clinic Ranking → Doctor Ranking → Revenue Forecast
    """
    return f"""
    {page_header("Executive Metrics", "C-suite revenue, operations, and ranking dashboards.")}
    <div class="flow">{flow}</div>
    {cards}
    <div class="card" style="margin-top:20px;">
        <h3>Sprint 5.9 Features</h3>
        <ul class="feature-list">{features}</ul>
    </div>
    """


def build_revenue_body() -> str:
    data = svc.revenue_metrics()
    rows = [
        [str(item["partner_id"]), str(item["invoices_paid"]), f"{item['revenue']:.2f}"]
        for item in data.get("top_partners_by_revenue", [])[:10]
    ]
    return f"""
    {page_header("Revenue", f"Period {data['period_start']} to {data['period_end']}.")}
    {metric_cards([
        ("Gross Revenue", data.get("gross_revenue", 0)),
        ("Invoices Paid", data.get("invoices_paid", 0)),
        ("Payment Total", data.get("payment_total", 0)),
        ("Invoices Total", data.get("invoices_total", 0)),
    ])}
    <div class="card"><h3>Top Partners by Revenue</h3>{_table(["Partner", "Invoices", "Revenue"], rows)}</div>
    """


def build_tat_body() -> str:
    data = svc.tat_metrics()
    return f"""
    {page_header("Turnaround Time", f"Period {data['period_start']} to {data['period_end']}.")}
    {metric_cards([
        ("Average TAT (hours)", data.get("average_tat_hours", 0)),
        ("Results Released", data.get("results_released", 0)),
        ("Lab Accession TAT (min)", data.get("lab_accession_tat_minutes", 0)),
    ])}
    <div class="card"><h3>KPI Metrics</h3><pre>{html.escape(json.dumps(data.get("kpi_metrics", {}), indent=2))}</pre></div>
    """


def build_orders_body() -> str:
    data = svc.orders_metrics()
    rows = [[status, str(count)] for status, count in sorted(data.get("by_status", {}).items())]
    return f"""
    {page_header("Orders", f"Period {data['period_start']} to {data['period_end']}.")}
    {metric_cards([
        ("Orders Total", data.get("orders_total", 0)),
        ("Completed", data.get("completed_orders", 0)),
        ("Pending", data.get("pending_orders", 0)),
    ])}
    <div class="card"><h3>Status Distribution</h3>{_table(["Status", "Count"], rows)}</div>
    """


def build_growth_body() -> str:
    data = svc.growth_metrics()
    growth = data["growth"]
    current = data["current_period"]
    previous = data["previous_period"]
    return f"""
    {page_header("Growth", "Period-over-period revenue and order momentum.")}
    {metric_cards([
        ("Revenue Growth %", growth["revenue_percent"]),
        ("Orders Growth %", growth["orders_percent"]),
        ("Revenue Delta", growth["revenue_delta"]),
        ("Orders Delta", growth["orders_delta"]),
    ])}
    <div class="card">
        <h3>Current Period</h3>
        <p>{current['start']} → {current['end']}</p>
        <p>Revenue: {current['gross_revenue']} · Orders: {current['orders_total']}</p>
    </div>
    <div class="card">
        <h3>Previous Period</h3>
        <p>{previous['start']} → {previous['end']}</p>
        <p>Revenue: {previous['gross_revenue']} · Orders: {previous['orders_total']}</p>
    </div>
    """


def build_lab_sla_body() -> str:
    data = svc.lab_sla_metrics()
    period = data["period_summary"]
    current = data["current_ops"]
    return f"""
    {page_header("Lab SLA", f"Period {data['period_start']} to {data['period_end']}.")}
    {metric_cards([
        ("SLA Compliance %", period.get("sla_compliance_percent", 0)),
        ("Average TAT (min)", period.get("average_tat_minutes", 0)),
        ("Accessions Completed", period.get("accessions_completed", 0)),
        ("SLA Breaches", period.get("sla_breaches", 0)),
        ("Pending Samples", current.get("pending_samples", 0)),
        ("Critical Open", current.get("critical_results_open", 0)),
    ])}
    """


def build_collector_sla_body() -> str:
    data = svc.collector_sla_metrics()
    rows = [
        [
            str(row["collector_id"]),
            str(row["orders_assigned"]),
            str(row["orders_completed"]),
            f"{row['completion_rate']:.1f}%",
        ]
        for row in data.get("collectors", [])[:15]
    ]
    return f"""
    {page_header("Collector SLA", f"Threshold {data.get('sla_threshold_percent', 90)}% completion.")}
    {metric_cards([
        ("Collectors Total", data.get("collectors_total", 0)),
        ("SLA Compliant", data.get("collectors_sla_compliant", 0)),
        ("Active Collectors", data.get("active_collectors", 0)),
    ])}
    <div class="card"><h3>Collector Performance</h3>{_table(["Collector", "Assigned", "Completed", "Rate"], rows)}</div>
    """


def build_clinic_ranking_body() -> str:
    data = svc.clinic_ranking()
    rows = [
        [
            str(row["rank"]),
            html.escape(str(row["name"])),
            str(row["orders"]),
            f"{row['revenue']:.2f}",
            str(row["referrals"]),
        ]
        for row in data.get("rankings", [])[:15]
    ]
    return f"""
    {page_header("Clinic Ranking", f"Period {data['period_start']} to {data['period_end']}.")}
    {metric_cards([("Clinics Ranked", data.get("clinics_ranked", 0))])}
    <div class="card"><h3>Top Clinics</h3>{_table(["Rank", "Clinic", "Orders", "Revenue", "Referrals"], rows)}</div>
    """


def build_doctor_ranking_body() -> str:
    data = svc.doctor_ranking()
    rows = [
        [
            str(row["rank"]),
            html.escape(str(row["name"])),
            html.escape(str(row.get("specialty") or "—")),
            str(row["referrals"]),
            str(row["approvals"]),
            str(row["score"]),
        ]
        for row in data.get("rankings", [])[:15]
    ]
    return f"""
    {page_header("Doctor Ranking", f"Period {data['period_start']} to {data['period_end']}.")}
    {metric_cards([("Doctors Ranked", data.get("doctors_ranked", 0))])}
    <div class="card"><h3>Top Doctors</h3>{_table(["Rank", "Doctor", "Specialty", "Referrals", "Approvals", "Score"], rows)}</div>
    """


def build_revenue_forecast_body() -> str:
    data = svc.revenue_forecast()
    historical = data["historical"]
    forecast = data["forecast"]
    return f"""
    {page_header("Revenue Forecast", data.get("methodology", ""))}
    {metric_cards([
        ("Historical Revenue", historical.get("gross_revenue", 0)),
        ("Daily Average", historical.get("daily_average", 0)),
        ("Pipeline Forecast", forecast.get("pipeline_opportunities", 0)),
        ("30-Day Trend", forecast.get("trend_projection_30d", 0)),
        ("Monthly Sales Won", forecast.get("monthly_sales_won", 0)),
        ("Combined Estimate", forecast.get("combined_estimate", 0)),
    ])}
    """
