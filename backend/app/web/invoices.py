from flask import Blueprint, request, redirect

from app.extensions.db import db
from app.models.invoice import Invoice
from app.models.company import Company
from app.models.order import Order


invoices_web_bp = Blueprint("invoices_web", __name__)


@invoices_web_bp.route("/invoices")
def invoices_page():

    invoices = Invoice.query.all()

    rows = ""

    for invoice in invoices:
        company = Company.query.get(invoice.company_id)
        order = Order.query.get(invoice.order_id)

        company_name = company.company_name if company else ""
        order_code = order.order_code if order else ""

        rows += f"""
        <tr>
            <td>{invoice.invoice_no}</td>
            <td>{company_name}</td>
            <td>{order_code}</td>
            <td>{invoice.total_amount:,.0f} VND</td>
            <td>{invoice.payment_status}</td>
<td>
    <a href="/payments/new?invoice_id={invoice.id}">
        Pay Now
    </a>
</td>
        </tr>
        """

    return f"""
    <html>
    <body style="font-family:Arial;background:#f1f5f9;padding:30px;">

        <h1>Invoices Management</h1>

        <a href="/invoices/new"
           style="background:#0d6efd;color:white;padding:10px 15px;text-decoration:none;border-radius:6px;">
           + New Invoice
        </a>

        <br><br>

        <table border="1" cellpadding="10" style="background:white;width:100%;">
            <tr>
                <th>Invoice No</th>
                <th>Company</th>
                <th>Order</th>
                <th>Total Amount</th>
                <th>Status</th>
            </tr>
            {rows}
        </table>

    </body>
    </html>
    """


@invoices_web_bp.route("/invoices/new", methods=["GET", "POST"])
def new_invoice():

    companies = Company.query.all()
    orders = Order.query.all()

    if request.method == "POST":

        invoice = Invoice(
            invoice_no=request.form.get("invoice_no"),
            company_id=request.form.get("company_id"),
            order_id=request.form.get("order_id"),
            total_amount=float(request.form.get("total_amount") or 0),
            payment_status="UNPAID"
        )

        db.session.add(invoice)
        db.session.commit()

        return redirect("/invoices")

    company_options = ""
    for company in companies:
        company_options += f"""
        <option value="{company.id}">
            {company.company_name}
        </option>
        """

    order_options = ""
    for order in orders:
        order_options += f"""
        <option value="{order.id}">
            {order.order_code}
        </option>
        """

    return f"""
    <html>
    <body style="font-family:Arial;background:#f1f5f9;padding:30px;">

        <h1>New Invoice</h1>

        <form method="POST">
            <input name="invoice_no" placeholder="Invoice No"><br><br>

            <select name="company_id">
                {company_options}
            </select><br><br>

            <select name="order_id">
                {order_options}
            </select><br><br>

            <input name="total_amount" placeholder="Total Amount"><br><br>

            <button type="submit">Save Invoice</button>
        </form>

    </body>
    </html>
    """
