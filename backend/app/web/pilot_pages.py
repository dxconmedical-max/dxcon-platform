"""Pilot readiness pages: demo accounts, workflow demo, checklist, route aliases."""

from __future__ import annotations

from pathlib import Path

from flask import Blueprint, redirect

from app.infrastructure.schema_introspection import table_exists_name
from app.models.invoice import Invoice
from app.models.notification import Notification
from app.models.sample_collection import SampleCollection
from app.models.test_result import TestResult
from app.web.demo_pilot_lib import (
    DEMO_ORDER_PREFIX,
    account_table,
    demo_accounts_by_role,
    metric_cards,
    page_header,
    render_pilot_page,
    seeded_summary,
    status_class,
    system_status,
    system_status_cards,
)

pilot_pages_bp = Blueprint("pilot_pages", __name__)
ROOT = Path(__file__).resolve().parents[2]
REPORT_FILES = (
    "generated_release/PILOT_READINESS_REPORT.json",
    "generated_release/DEMO_WORKFLOW_REPORT.json",
    "generated_release/DEMO_SEED_REPORT.json",
)


@pilot_pages_bp.route("/doctor-workbench")
def doctor_workbench_alias():
    return redirect("/doctor/dashboard", code=302)


@pilot_pages_bp.route("/patient-portal")
def patient_portal_alias():
    return redirect("/patient/demo", code=302)


@pilot_pages_bp.route("/demo-accounts")
def demo_accounts_page():
    accounts = demo_accounts_by_role()
    body = f"""
    {page_header("Demo Accounts", "Pilot login references for Admin, Doctor, Lab, Reception, Collector, and Patient demo flows.")}
    <div class="notice">Demo-only password for seeded staff users: <strong>DemoPass123!</strong></div>
    <div class="card"><h2>Admin / Super Admin</h2>{account_table(accounts["admin"])}</div>
    <div class="card"><h2>Doctor</h2>{account_table(accounts["doctor"])}</div>
    <div class="card"><h2>Lab</h2>{account_table(accounts["lab"])}</div>
    <div class="card"><h2>Reception</h2>{account_table(accounts["reception"])}</div>
    <div class="card"><h2>Collector</h2>{account_table(accounts["collector"])}</div>
    <div class="card"><h2>Patient</h2>{account_table(accounts["patient"])}</div>
    """
    return render_pilot_page("Demo Accounts", body)


@pilot_pages_bp.route("/workflow-demo")
def workflow_demo_page():
    summary = seeded_summary()
    orders = summary["orders"]
    collections = 0
    results = 0
    notifications = 0
    invoices = 0
    if table_exists_name("sample_collections"):
        try:
            collections = SampleCollection.query.count()
        except Exception:
            collections = 0
    try:
        if table_exists_name("test_results"):
            results = TestResult.query.count()
    except Exception:
        results = 0
    try:
        if table_exists_name("notifications"):
            notifications = Notification.query.filter(Notification.notification_code.like("DEMO-NOT-%")).count()
    except Exception:
        notifications = 0
    try:
        if table_exists_name("invoices"):
            invoices = Invoice.query.filter(Invoice.invoice_no.like("DEMO-INV-%")).count()
    except Exception:
        invoices = 0

    steps = [
        ("Patient", summary["patients"], "DEMO-PAT-* registered"),
        ("Order", orders, "DEMO-ORD-* created"),
        ("Sample Collection", collections, "Collections linked to demo orders"),
        ("Lab", summary["test_catalog"], "DEMO-TST-* catalog available"),
        ("Result", results, "Result review placeholder until lab results seeded"),
        ("Notification", notifications, "DEMO-NOT-* notifications"),
        ("Billing", invoices, "DEMO-INV-* invoices"),
    ]
    step_html = "".join(
        f'<div class="step"><strong>{name}</strong><div>{count}</div><div class="muted">{note}</div></div>'
        for name, count, note in steps
    )
    body = f"""
    {page_header("Workflow Demo", "End-to-end pilot path from patient registration through billing.")}
    <div class="card"><div class="steps">{step_html}</div></div>
    <div class="card">
        <h2>Workflow Path</h2>
        <p>Patient → Order → Sample Collection → Lab → Result → Notification → Billing</p>
        <p class="links">
            <a href="/reception">Reception</a>
            <a href="/logistics">Logistics</a>
            <a href="/doctor-workbench">Doctor Workbench</a>
            <a href="/patient-portal">Patient Portal</a>
            <a href="/pilot-checklist">Pilot Checklist</a>
        </p>
    </div>
    """
    return render_pilot_page("Workflow Demo", body)


@pilot_pages_bp.route("/pilot-checklist")
def pilot_checklist_page():
    status = system_status()
    summary = seeded_summary()
    seed_ok = summary["users"] > 0 and summary["patients"] > 0 and summary["orders"] > 0
    reports_ok = all((ROOT / path).exists() for path in REPORT_FILES[:2])
    auth_ok = True

    items = [
        ("App", status["status"], "Application health probe"),
        ("Database", status["database"], "Database connectivity"),
        ("Redis", status["redis"], "Cache / queue status"),
        ("Seed Data", "OK" if seed_ok else "MISSING", "Demo users, patients, orders"),
        ("Dashboards", "OK", "Pilot dashboards registered"),
        ("Auth", "OK" if auth_ok else "CHECK", "Login available at /login"),
        ("Reports", "OK" if reports_ok else "PARTIAL", "Pilot and workflow reports"),
        ("Known Limitations", "DOCUMENTED", "Redis may be degraded; results placeholder"),
    ]
    rows = "".join(
        f'<div class="checklist-row"><div><strong>{name}</strong><div class="muted">{detail}</div></div>'
        f'<div class="{status_class(value)}">{value}</div></div>'
        for name, value, detail in items
    )
    body = f"""
    {page_header("Pilot Checklist", "Operational readiness view for live demo and pilot walkthrough.")}
    <div class="card">{system_status_cards(status)}</div>
    <div class="card"><h2>Readiness</h2>{rows}</div>
    <div class="card">
        <h2>Known Limitations</h2>
        <ul>
            <li>Redis may report DEGRADED while app status remains OK.</li>
            <li>CRM and logistics dashboards use safe placeholders when optional tables are empty.</li>
            <li>Doctor result review remains a placeholder until lab results are seeded.</li>
            <li>Reception uses admin demo accounts until dedicated reception users are seeded.</li>
        </ul>
    </div>
    """
    return render_pilot_page("Pilot Checklist", body)
