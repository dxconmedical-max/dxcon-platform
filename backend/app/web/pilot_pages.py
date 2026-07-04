"""Pilot readiness pages: demo accounts, workflow demo, checklist, route aliases."""

from __future__ import annotations

from pathlib import Path

from flask import Blueprint

from app.web.demo_pilot_lib import (
    account_table,
    demo_accounts_by_role,
    page_header,
    render_pilot_page,
    seeded_summary,
    status_class,
    system_status,
    system_status_cards,
)
from app.web.pilot_dashboard_data import build_doctor_workbench_body, build_patient_portal_body, build_workflow_demo_body

pilot_pages_bp = Blueprint("pilot_pages", __name__)
ROOT = Path(__file__).resolve().parents[2]
REPORT_FILES = (
    "generated_release/PILOT_READINESS_REPORT.json",
    "generated_release/DASHBOARD_STATUS.json",
    "generated_release/WORKFLOW_STATUS.json",
    "generated_release/DEMO_SEED_REPORT.json",
)


@pilot_pages_bp.route("/doctor-workbench")
def doctor_workbench_page():
    return render_pilot_page("Doctor Workbench", build_doctor_workbench_body())


@pilot_pages_bp.route("/patient-portal")
def patient_portal_page():
    return render_pilot_page("Patient Portal", build_patient_portal_body())


@pilot_pages_bp.route("/demo-accounts")
def demo_accounts_page():
    accounts = demo_accounts_by_role()
    body = f"""
    {page_header("Demo Accounts", "Pilot login references for all operational roles. Demo-only passwords are shown; others are masked.")}
    <div class="notice">Demo-only password for seeded staff users: <strong>DemoPass123!</strong></div>
    <div class="card"><h2>SUPER_ADMIN / ADMIN</h2>{account_table(accounts["admin"])}</div>
    <div class="card"><h2>RECEPTION</h2>{account_table(accounts["reception"])}</div>
    <div class="card"><h2>DOCTOR</h2>{account_table(accounts["doctor"][:15])}</div>
    <div class="card"><h2>LAB</h2>{account_table(accounts["lab"][:10])}</div>
    <div class="card"><h2>COLLECTOR</h2>{account_table(accounts["collector"][:10])}</div>
    <div class="card"><h2>PATIENT</h2>{account_table(accounts["patient"], reveal_demo_passwords=False)}</div>
    """
    return render_pilot_page("Demo Accounts", body)


@pilot_pages_bp.route("/workflow-demo")
def workflow_demo_page():
    return render_pilot_page("Workflow Timeline", build_workflow_demo_body())


@pilot_pages_bp.route("/pilot-checklist")
def pilot_checklist_page():
    status = system_status()
    summary = seeded_summary()
    seed_ok = summary["users"] > 0 and summary["patients"] > 0 and summary["orders"] > 0
    reports_ok = all((ROOT / path).exists() for path in REPORT_FILES[:3])

    items = [
        ("App", status["status"], "Application health probe"),
        ("Database", status["database"], "Database connectivity"),
        ("Redis", status["redis"], "Cache / queue status"),
        ("Seed Data", "OK" if seed_ok else "MISSING", "Demo users, patients, orders"),
        ("Dashboards", "OK", "Phase 3A pilot dashboards registered"),
        ("Auth", "OK", "Login available at /login"),
        ("Reports", "OK" if reports_ok else "PARTIAL", "Pilot, dashboard, and workflow reports"),
        ("Phase", "3A", "Operational medical platform pilot"),
    ]
    rows = "".join(
        f'<div class="checklist-row"><div><strong>{name}</strong><div class="muted">{detail}</div></div>'
        f'<div class="{status_class(value)}">{value}</div></div>'
        for name, value, detail in items
    )
    body = f"""
    {page_header("Pilot Checklist", "Phase 3A operational readiness for live demo and pilot walkthrough.")}
    <div class="card">{system_status_cards(status)}</div>
    <div class="card"><h2>Readiness</h2>{rows}</div>
    """
    return render_pilot_page("Pilot Checklist", body)
