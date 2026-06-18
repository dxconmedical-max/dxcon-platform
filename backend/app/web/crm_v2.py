from flask import Blueprint

from app.models.crm_lead import CrmLead
from app.models.company import Company
from app.models.contract import Contract
from app.models.invoice import Invoice
from app.models.payment import Payment


crm_v2_web_bp = Blueprint("crm_v2_web", __name__)


@crm_v2_web_bp.route("/crm-pipeline")
def crm_pipeline():

    leads = CrmLead.query.all()
    companies = Company.query.all()
    contracts = Contract.query.all()
    invoices = Invoice.query.all()
    payments = Payment.query.all()

    revenue = sum([(p.amount or 0) for p in payments])

    lead_rows = ""
    for l in leads:
        lead_rows += f"""
        <tr>
            <td>{getattr(l, "lead_name", "") or getattr(l, "name", "")}</td>
            <td>{getattr(l, "phone", "")}</td>
            <td>{getattr(l, "status", "")}</td>
            <td>{getattr(l, "source", "")}</td>
        </tr>
        """

    company_rows = ""
    for c in companies:
        company_rows += f"""
        <tr>
            <td>{c.company_code}</td>
            <td>{c.company_name}</td>
            <td>{c.phone or ""}</td>
            <td>{c.status}</td>
        </tr>
        """

    contract_rows = ""
    for c in contracts:
        contract_rows += f"""
        <tr>
            <td>{c.contract_code}</td>
            <td>{c.title}</td>
            <td>{c.status}</td>
            <td>{c.total_value:,.0f}</td>
        </tr>
        """

    return f"""
    <html>
    <body style="font-family:Arial;background:#f1f5f9;padding:30px;">
        <h1>DxCon CRM Pipeline V2</h1>

        <div style="display:flex;gap:15px;flex-wrap:wrap;">
            <div style="background:white;padding:20px;border-radius:12px;width:220px;"><h3>Leads</h3><h1>{len(leads)}</h1></div>
            <div style="background:white;padding:20px;border-radius:12px;width:220px;"><h3>Companies</h3><h1>{len(companies)}</h1></div>
            <div style="background:white;padding:20px;border-radius:12px;width:220px;"><h3>Contracts</h3><h1>{len(contracts)}</h1></div>
            <div style="background:white;padding:20px;border-radius:12px;width:220px;"><h3>Revenue</h3><h1>{revenue:,.0f}</h1></div>
        </div>

        <h2>Leads</h2>
        <table border="1" cellpadding="10" style="background:white;width:100%;border-collapse:collapse;">
            <tr><th>Name</th><th>Phone</th><th>Status</th><th>Source</th></tr>
            {lead_rows}
        </table>

        <h2>Companies</h2>
        <table border="1" cellpadding="10" style="background:white;width:100%;border-collapse:collapse;">
            <tr><th>Code</th><th>Name</th><th>Phone</th><th>Status</th></tr>
            {company_rows}
        </table>

        <h2>Contracts</h2>
        <table border="1" cellpadding="10" style="background:white;width:100%;border-collapse:collapse;">
            <tr><th>Code</th><th>Title</th><th>Status</th><th>Value</th></tr>
            {contract_rows}
        </table>

        <br>
        <a href="/finance">Finance</a> |
        <a href="/executive">Executive</a>
    </body>
    </html>
    """
