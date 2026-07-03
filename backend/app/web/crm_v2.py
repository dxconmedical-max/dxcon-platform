from flask import Blueprint

from app.infrastructure.schema_introspection import table_exists_name
from app.models.company import Company
from app.models.contract import Contract
from app.models.crm_lead import CrmLead
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.web.demo_pilot_lib import metric_cards, render_pilot_page, seeded_summary

crm_v2_web_bp = Blueprint("crm_v2_web", __name__)


@crm_v2_web_bp.route("/crm-pipeline")
def crm_pipeline():
    summary = seeded_summary()
    has_leads = table_exists_name("crm_leads")
    placeholder = ""

    if not has_leads:
        placeholder = """
        <div class="notice">
            CRM lead/opportunity tables are not present in this environment.
            Showing demo company and billing placeholders from seeded data instead.
        </div>
        """
        leads = []
    else:
        try:
            leads = CrmLead.query.all()
        except Exception:
            leads = []
            placeholder = """
            <div class="notice">
                CRM tables exist but could not be queried safely. Showing demo billing summary only.
            </div>
            """

    companies = Company.query.all() if table_exists_name("companies") else []
    contracts = Contract.query.all() if table_exists_name("contracts") else []
    payments = Payment.query.all() if table_exists_name("payments") else []
    revenue = sum([(p.amount or 0) for p in payments])

    lead_rows = "".join(
        f"<tr><td>{getattr(l, 'lead_name', '') or getattr(l, 'name', '')}</td>"
        f"<td>{getattr(l, 'phone', '')}</td><td>{getattr(l, 'status', '')}</td>"
        f"<td>{getattr(l, 'source', '')}</td></tr>"
        for l in leads
    ) or "<tr><td colspan='4'>No CRM leads seeded. Demo billing entities are available below.</td></tr>"

    company_rows = "".join(
        f"<tr><td>{c.company_code}</td><td>{c.company_name}</td><td>{c.phone or ''}</td><td>{c.status}</td></tr>"
        for c in companies
    ) or "<tr><td colspan='4'>No companies found.</td></tr>"

    contract_rows = "".join(
        f"<tr><td>{c.contract_code}</td><td>{c.title}</td><td>{c.status}</td><td>{c.total_value:,.0f}</td></tr>"
        for c in contracts
    ) or "<tr><td colspan='4'>No contracts found.</td></tr>"

    body = f"""
    <h1>CRM Pipeline</h1>
    <p style="color:#475569;">Sales pipeline view with graceful fallback when CRM tables are unavailable.</p>
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
    <table><tr><th>Name</th><th>Phone</th><th>Status</th><th>Source</th></tr>{lead_rows}</table></div>
    <div class="card"><h2>Companies</h2>
    <table><tr><th>Code</th><th>Name</th><th>Phone</th><th>Status</th></tr>{company_rows}</table></div>
    <div class="card"><h2>Contracts</h2>
    <table><tr><th>Code</th><th>Title</th><th>Status</th><th>Value</th></tr>{contract_rows}</table></div>
    """
    return render_pilot_page("CRM Pipeline", body)
