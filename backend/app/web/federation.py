from flask import Blueprint

from app.models.federation_capacity import CapacitySnapshot
from app.models.federation_core import FederatedLab, FederationProvider
from app.models.federation_failover import FailoverEvent
from app.models.federation_routing import RoutingDecision
from app.services.federation_service import FederationDashboardService


federation_web_bp = Blueprint("federation_web", __name__)


def _styles():
    return """
    body { margin:0; font-family:Arial,sans-serif; background:#f8fafc; color:#0f172a; }
    .layout { display:flex; min-height:100vh; }
    .sidebar { width:220px; background:#1e293b; color:white; padding:24px; }
    .sidebar a { display:block; color:white; text-decoration:none; padding:12px 0; border-bottom:1px solid rgba(255,255,255,.12); }
    .content { flex:1; padding:32px; }
    .card { background:white; border-radius:12px; padding:24px; box-shadow:0 4px 12px rgba(0,0,0,.08); margin-bottom:24px; }
    .grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:16px; }
    .metric { background:#e0f2fe; border-radius:12px; padding:16px; }
    .metric strong { display:block; font-size:24px; }
    table { width:100%; border-collapse:collapse; }
    th, td { padding:12px; border-bottom:1px solid #e5e7eb; text-align:left; font-size:14px; }
    th { background:#e2e8f0; }
    """


def _sidebar(active):
    links = [
        ("/federation", "Overview"),
        ("/federation/labs", "Labs"),
        ("/federation/capacity", "Capacity"),
        ("/federation/routing", "Routing"),
        ("/federation/failover", "Failover"),
    ]
    items = ""
    for href, label in links:
        cls = ' style="font-weight:bold;"' if href == active else ""
        items += f'<a href="{href}"{cls}>{label}</a>'
    return f'<div class="sidebar"><h2>Federation</h2>{items}</div>'


def _metric_cards(metrics):
    cards = ""
    for label, value in metrics:
        cards += f'<div class="metric"><span>{label}</span><strong>{value}</strong></div>'
    return f'<div class="grid">{cards}</div>'


@federation_web_bp.route("/federation")
def federation_home():
    metrics = FederationDashboardService.get_metrics()
    return f"""
    <html><head><title>Federation Dashboard</title><style>{_styles()}</style></head><body>
    <div class="layout">{_sidebar("/federation")}<div class="content">
    <div class="card"><h1>Multi-Lab Federation</h1>
    {_metric_cards([
        ("Labs Online", metrics["labs_online"]),
        ("Labs Offline", metrics["labs_offline"]),
        ("Daily Workload", metrics["daily_workload"]),
        ("Remaining Capacity", metrics["remaining_capacity"]),
        ("Routing Decisions", metrics["routing_decisions"]),
        ("Failover Events", metrics["failover_events"]),
        ("SLA Compliance", f'{metrics["sla_compliance"]}%'),
        ("Average TAT (h)", metrics["average_tat_hours"]),
        ("QC Issue Rate", f'{metrics["qc_issue_rate"]}%'),
    ])}
    </div></div></div></body></html>
    """


@federation_web_bp.route("/federation/labs")
def federation_labs():
    labs = FederatedLab.query.order_by(FederatedLab.created_at.desc()).limit(50).all()
    providers = {p.id: p.name for p in FederationProvider.query.all()}
    rows = ""
    for lab in labs:
        rows += f"""<tr>
            <td>{lab.lab_code}</td><td>{lab.name}</td>
            <td>{providers.get(lab.provider_id, "")}</td>
            <td>{lab.city or ""}</td><td>{lab.status}</td><td>{lab.connection_status}</td>
        </tr>"""
    return f"""
    <html><head><title>Federation Labs</title><style>{_styles()}</style></head><body>
    <div class="layout">{_sidebar("/federation/labs")}<div class="content">
    <div class="card"><h1>Federated Labs</h1>
    <table><tr><th>Code</th><th>Name</th><th>Provider</th><th>City</th><th>Status</th><th>Connection</th></tr>
    {rows or "<tr><td colspan='6'>No labs</td></tr>"}</table>
    </div></div></div></body></html>
    """


@federation_web_bp.route("/federation/capacity")
def federation_capacity():
    snapshots = CapacitySnapshot.query.order_by(CapacitySnapshot.snapshot_date.desc()).limit(30).all()
    lab_map = {lab.id: lab.lab_code for lab in FederatedLab.query.all()}
    rows = ""
    for snap in snapshots:
        rows += f"""<tr>
            <td>{lab_map.get(snap.federated_lab_id, snap.federated_lab_id)}</td>
            <td>{snap.snapshot_date}</td><td>{snap.total_capacity}</td>
            <td>{snap.used_capacity}</td><td>{snap.remaining_capacity}</td><td>{snap.utilization_rate}%</td>
        </tr>"""
    return f"""
    <html><head><title>Federation Capacity</title><style>{_styles()}</style></head><body>
    <div class="layout">{_sidebar("/federation/capacity")}<div class="content">
    <div class="card"><h1>Capacity Snapshots</h1>
    <table><tr><th>Lab</th><th>Date</th><th>Total</th><th>Used</th><th>Remaining</th><th>Utilization</th></tr>
    {rows or "<tr><td colspan='6'>No snapshots</td></tr>"}</table>
    </div></div></div></body></html>
    """


@federation_web_bp.route("/federation/routing")
def federation_routing():
    decisions = RoutingDecision.query.order_by(RoutingDecision.created_at.desc()).limit(30).all()
    lab_map = {lab.id: lab.lab_code for lab in FederatedLab.query.all()}
    rows = ""
    for decision in decisions:
        rows += f"""<tr>
            <td>{decision.decision_code}</td><td>{decision.test_code or ""}</td>
            <td>{lab_map.get(decision.selected_lab_id, "")}</td>
            <td>{decision.score_total}</td><td>{decision.candidate_count}</td><td>{decision.created_at}</td>
        </tr>"""
    return f"""
    <html><head><title>Federation Routing</title><style>{_styles()}</style></head><body>
    <div class="layout">{_sidebar("/federation/routing")}<div class="content">
    <div class="card"><h1>Routing Decisions</h1>
    <table><tr><th>Code</th><th>Test</th><th>Selected Lab</th><th>Score</th><th>Candidates</th><th>At</th></tr>
    {rows or "<tr><td colspan='6'>No decisions</td></tr>"}</table>
    </div></div></div></body></html>
    """


@federation_web_bp.route("/federation/failover")
def federation_failover():
    events = FailoverEvent.query.order_by(FailoverEvent.created_at.desc()).limit(30).all()
    lab_map = {lab.id: lab.lab_code for lab in FederatedLab.query.all()}
    rows = ""
    for event in events:
        rows += f"""<tr>
            <td>{event.event_code}</td><td>{event.trigger_type}</td>
            <td>{lab_map.get(event.source_lab_id, "")}</td>
            <td>{lab_map.get(event.fallback_lab_id, "")}</td>
            <td>{event.status}</td><td>{event.message or ""}</td>
        </tr>"""
    return f"""
    <html><head><title>Federation Failover</title><style>{_styles()}</style></head><body>
    <div class="layout">{_sidebar("/federation/failover")}<div class="content">
    <div class="card"><h1>Failover Events</h1>
    <table><tr><th>Code</th><th>Trigger</th><th>Source</th><th>Fallback</th><th>Status</th><th>Message</th></tr>
    {rows or "<tr><td colspan='6'>No events</td></tr>"}</table>
    </div></div></div></body></html>
    """
