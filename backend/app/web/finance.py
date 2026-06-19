from app.core.web_authz import web_roles_required
from flask import Blueprint

from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.order import Order


finance_web_bp = Blueprint("finance_web", __name__)

@web_roles_required(
    "SUPER_ADMIN",
    "ADMIN",
    "ACCOUNTING"
)
@finance_web_bp.route("/finance")
@web_roles_required("SUPER_ADMIN", "ADMIN", "ACCOUNTING")
def finance_dashboard():

    invoices = Invoice.query.all()
    payments = Payment.query.all()
    orders = Order.query.all()

    total_revenue = sum([(p.amount or 0) for p in payments])
    total_invoice = sum([(i.total_amount or 0) for i in invoices])
    unpaid = sum([(i.total_amount or 0) for i in invoices if i.payment_status != "PAID"])

    invoice_rows = ""

    for i in invoices:
        invoice_rows += f"""
        <tr>
            <td>{i.invoice_no}</td>
            <td>{i.total_amount:,.0f}</td>
            <td>{i.payment_status}</td>
            <td>{i.created_at}</td>
        </tr>
        """

    payment_rows = ""

    for p in payments:
        payment_rows += f"""
        <tr>
            <td>{p.amount:,.0f}</td>
            <td>{p.payment_method}</td>
            <td>{p.status}</td>
            <td>{p.payment_date}</td>
        </tr>
        """

    return f"""
    <html>
    <body style="font-family:Arial;background:#f1f5f9;padding:30px;">
        <h1>DxCon Finance Dashboard</h1>

        <div style="display:flex;gap:15px;flex-wrap:wrap;">
            <div style="background:white;padding:20px;border-radius:12px;width:220px;">
                <h3>Total Revenue</h3><h1>{total_revenue:,.0f}</h1>
            </div>
            <div style="background:white;padding:20px;border-radius:12px;width:220px;">
                <h3>Total Invoice</h3><h1>{total_invoice:,.0f}</h1>
            </div>
            <div style="background:white;padding:20px;border-radius:12px;width:220px;">
                <h3>Outstanding</h3><h1>{unpaid:,.0f}</h1>
            </div>
            <div style="background:white;padding:20px;border-radius:12px;width:220px;">
                <h3>Orders</h3><h1>{len(orders)}</h1>
            </div>
        </div>

        <h2>Invoices</h2>
        <table border="1" cellpadding="10" style="background:white;width:100%;border-collapse:collapse;">
            <tr><th>Invoice</th><th>Amount</th><th>Status</th><th>Created</th></tr>
            {invoice_rows}
        </table>

        <h2>Payments</h2>
        <table border="1" cellpadding="10" style="background:white;width:100%;border-collapse:collapse;">
            <tr><th>Amount</th><th>Method</th><th>Status</th><th>Date</th></tr>
            {payment_rows}
        </table>

        <br>
        <a href="/executive">Executive</a> |
        <a href="/crm">CRM</a> |
        <a href="/dashboard">Dashboard</a>
    </body>
    </html>
    """
