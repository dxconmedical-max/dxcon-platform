import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import create_app
from app.models.user import User
from app.models.patient import Patient
from app.models.order import Order
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.result_file import ResultFile
from app.models.audit_log import AuditLog

app = create_app()

with app.app_context():

    print("\n=== DXCON DATABASE STATUS ===\n")

    print("Users       :", User.query.count())
    print("Patients    :", Patient.query.count())
    print("Orders      :", Order.query.count())
    print("Invoices    :", Invoice.query.count())
    print("Payments    :", Payment.query.count())
    print("ResultFiles :", ResultFile.query.count())
    print("AuditLogs   :", AuditLog.query.count())

    print("\nDATABASE CHECK DONE\n")
