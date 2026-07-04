from flask import Blueprint

from app.infrastructure.schema_introspection import table_exists_name
from app.models.company import Company
from app.models.contract import Contract
from app.models.crm_lead import CrmLead
from app.models.payment import Payment
from app.web.demo_pilot_lib import (
    metric_cards,
    page_header,
    render_pilot_page,
    render_safe_page,
    safe_all,
    seeded_summary,
)

crm_v2_web_bp = Blueprint("crm_v2_web", __name__)


def _build_crm_body() -> str:
    summary = seeded_summary()
    placeholder = ""
    leads: list = []

    if table_exists_name("crm_leads"):
        leads = safe_all(CrmLead)
        if not leads:
            placeholder = """
            <div class="notice">
                CRM lead tables exist but no leads are seeded yet. Showing demo companies and billing context below.
            </div>
            """
    else:
        placeholder = """
        <div class="notice">
            CRM lead/opportunity tables are not present in this environment.
            Showing demo company and billing placeholders from seeded data instead.
        </div>
        """

    companies = safe_all(Company) if table_exists_name("companies") else []
    contracts = safe_all(Contract) if table_exists_name("contracts") else []
    payments = safe_all(Payment) if table_exists_name("payments") else []
    revenue = sum((p.amount or 0) for p in payments)

    lead_rows = "".join(
        f"<tr><td>{getattr(l, 'contact_person', '') or getattr(l, 'company_name', '')}</td>"
        f"<td>{getattr(l, 'phone', '')}</td><td>{getattr(l, 'status', '')}</td>"
        f"<td>{getattr(l, 'lead_source', '')}</td></tr>"
        for l in leads
    ) or "<tr><td colspan='4'>No CRM leads seeded. Demo billing entities are available below.</td></tr>"

    company_rows = "".join(
        f"<tr><td>{c.company_code}</td><td>{c.company_name}</td><td>{c.phone or ''}</td><td>{c.status}</td></tr>"
        for c in companies
    ) or "<tr><td colspan='4'>No companies found.</td></tr>"

    contract_rows = "".join(
        f"<tr><td>{c.contract_code}</td><td>{c.title}</td><td>{c.status}</td><td>{(c.total_value or 0):,.0f}</td></tr>"
        for c in contracts
    ) or "<tr><td colspan='4'>No contracts found.</td></tr>"

    return f"""
    {page_header("CRM Pipeline", "Sales pipeline with safe fallback when CRM tables or leads are unavailable.")}
    {placeholder}
    {metric_cards([
        ("Leads", len(leads)),
        ("Companies", len(companies)),
        ("Contracts", len(contracts)),
        ("Revenue", f"{revenue:,.0f}"),
    ])}
    <div class="card">
        <h2>Seeded Demo Context</h2>
        {metric_cards([
            ("Demo Patients", summary["patients"]),
            ("Demo Orders", summary["orders"]),
            ("Demo Tests", summary["test_catalog"]),
            ("Demo Users", summary["users"]),
        ])}
    </div>
    <div class="card"><h2>Leads / Opportunities</h2>
    <table><tr><th>Contact</th><th>Phone</th><th>Status</th><th>Source</th></tr>{lead_rows}</table></div>
    <div class="card"><h2>Companies</h2>
    <table><tr><th>Code</th><th>Name</th><th>Phone</th><th>Status</th></tr>{company_rows}</table></div>
    <div class="card"><h2>Contracts</h2>
    <table><tr><th>Code</th><th>Title</th><th>Status</th><th>Value</th></tr>{contract_rows}</table></div>
    """


@crm_v2_web_bp.route("/crm-pipeline")
def crm_pipeline():
    return render_safe_page(
        "CRM Pipeline",
        "Sales pipeline with safe fallback when CRM tables or leads are unavailable.",
        _build_crm_body,
    )
