from flask import Blueprint, request, redirect

from app.extensions.db import db
from app.models.payment import Payment
from app.models.invoice import Invoice
from app.core.audit import write_audit

payments_web_bp = Blueprint("payments_web", __name__)


@payments_web_bp.route("/payments")
def payments_page():

    payments = Payment.query.all()

    rows = ""

    for payment in payments:
        invoice = Invoice.query.get(payment.invoice_id)
        invoice_no = invoice.invoice_no if invoice else ""

        rows += f"""
        <tr>
            <td>{invoice_no}</td>
            <td>{payment.amount:,.0f} VND</td>
            <td>{payment.payment_method}</td>
            <td>{payment.status}</td>
            <td>{payment.payment_date}</td>
        </tr>
        """

    return f"""
    <html>
    <body style="font-family:Arial;background:#f1f5f9;padding:30px;">

        <h1>Payments Management</h1>

        <a href="/payments/new"
           style="background:#0d6efd;color:white;padding:10px 15px;text-decoration:none;border-radius:6px;">
           + New Payment
        </a>

        <br><br>

        <table border="1" cellpadding="10" style="background:white;width:100%;">
            <tr>
                <th>Invoice</th>
                <th>Amount</th>
                <th>Method</th>
                <th>Status</th>
                <th>Date</th>
            </tr>
            {rows}
        </table>

        <br>
        <a href="/dashboard">Back to Dashboard</a>

    </body>
    </html>
    """


@payments_web_bp.route("/payments/new", methods=["GET", "POST"])
def new_payment():

    selected_invoice_id = request.args.get("invoice_id")

    invoices = Invoice.query.all()

    if request.method == "POST":

        invoice_id = request.form.get("invoice_id")

        invoice = Invoice.query.get(invoice_id)

        amount = float(request.form.get("amount") or 0)

        if invoice and amount == 0:
            amount = invoice.total_amount or 0

        payment = Payment(
            invoice_id=invoice_id,
            amount=amount,
            payment_method=request.form.get("payment_method") or "BANK_TRANSFER",
            status="PAID"
        )

        db.session.add(payment)

        if invoice:
            invoice.payment_status = "PAID"

        db.session.commit()

        write_audit(
            action="CREATE_PAYMENT",
            object_type="PAYMENT",
            object_id=payment.id,
            user_email="WEB"
        )

        db.session.commit()
        return redirect("/payments")

    invoice_options = ""

    selected_invoice = None

    for invoice in invoices:

        selected = ""

        if selected_invoice_id == invoice.id:
            selected = "selected"
            selected_invoice = invoice

        invoice_options += f"""
        <option value="{invoice.id}" {selected}>
            {invoice.invoice_no} - {invoice.total_amount:,.0f} VND
        </option>
        """

    default_amount = ""

    if selected_invoice:
        default_amount = selected_invoice.total_amount or 0

    return f"""
    <html>
    <body style="font-family:Arial;background:#f1f5f9;padding:30px;">

        <h1>New Payment</h1>

        <form method="POST">
            <label>Invoice</label><br>
            <select name="invoice_id">
                {invoice_options}
            </select><br><br>

            <label>Amount</label><br>
            <input name="amount" value="{default_amount}" placeholder="Amount"><br><br>

            <label>Payment Method</label><br>
            <select name="payment_method">
                <option value="BANK_TRANSFER">Bank Transfer</option>
                <option value="CASH">Cash</option>
                <option value="CARD">Card</option>
            </select><br><br>

            <button type="submit">Save Payment</button>
        </form>

        <br>
        <a href="/invoices">Back to Invoices</a>

    </body>
    </html>
    """
