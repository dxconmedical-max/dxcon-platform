from pathlib import Path

files = {
"app/models/shipment.py": r'''
from app.extensions.db import db
from datetime import datetime
import uuid


class Shipment(db.Model):
    __tablename__ = "shipments"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    shipment_code = db.Column(db.String(100), unique=True, nullable=False)

    collector_id = db.Column(db.String(36))
    transport_box_id = db.Column(db.String(36))
    lab_name = db.Column(db.String(255))

    status = db.Column(db.String(50), default="CREATED")
    sample_count = db.Column(db.Integer, default=0)

    temperature = db.Column(db.String(50))
    gps_location = db.Column(db.String(255))

    departed_at = db.Column(db.DateTime)
    arrived_at = db.Column(db.DateTime)
    received_at = db.Column(db.DateTime)

    received_by = db.Column(db.String(255))
    receiver_note = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def qr_payload(self):
        return f"DXCON:SHIPMENT:{self.shipment_code}"

    def to_dict(self):
        return {
            "id": self.id,
            "shipment_code": self.shipment_code,
            "qr_payload": self.qr_payload(),
            "collector_id": self.collector_id,
            "transport_box_id": self.transport_box_id,
            "lab_name": self.lab_name,
            "status": self.status,
            "sample_count": self.sample_count,
            "temperature": self.temperature,
            "gps_location": self.gps_location,
            "departed_at": self.departed_at.isoformat() if self.departed_at else None,
            "arrived_at": self.arrived_at.isoformat() if self.arrived_at else None,
            "received_at": self.received_at.isoformat() if self.received_at else None,
            "received_by": self.received_by,
            "receiver_note": self.receiver_note,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
''',

"app/api/shipments/routes.py": r'''
from flask import Blueprint, request
from datetime import datetime

from app.extensions.db import db
from app.models.shipment import Shipment
from app.core.audit import write_audit


shipments_bp = Blueprint(
    "shipments",
    __name__,
    url_prefix="/api/v1/shipments"
)


def next_shipment_code():
    count = Shipment.query.count() + 1
    return f"DXCON-SHIP-{datetime.utcnow().strftime('%Y%m%d')}-{count:04d}"


def find_shipment(shipment_id):
    return Shipment.query.get(shipment_id) or Shipment.query.filter_by(
        shipment_code=shipment_id
    ).first()


@shipments_bp.route("", methods=["GET"])
def list_shipments():
    items = Shipment.query.order_by(
        Shipment.created_at.desc()
    ).all()

    return {
        "count": len(items),
        "shipments": [x.to_dict() for x in items]
    }


@shipments_bp.route("", methods=["POST"])
def create_shipment():
    data = request.json or {}

    item = Shipment(
        shipment_code=data.get("shipment_code") or next_shipment_code(),
        collector_id=data.get("collector_id"),
        transport_box_id=data.get("transport_box_id"),
        lab_name=data.get("lab_name"),
        sample_count=int(data.get("sample_count") or 0),
        temperature=data.get("temperature"),
        gps_location=data.get("gps_location"),
        status="CREATED"
    )

    db.session.add(item)
    db.session.commit()

    write_audit(
        action="CREATE_SHIPMENT",
        object_type="SHIPMENT",
        object_id=item.id,
        user_email=data.get("created_by") or "SYSTEM"
    )
    db.session.commit()

    return {
        "success": True,
        "shipment": item.to_dict()
    }, 201


@shipments_bp.route("/<shipment_id>", methods=["GET"])
def get_shipment(shipment_id):
    item = find_shipment(shipment_id)

    if not item:
        return {"error": "shipment not found"}, 404

    return item.to_dict()


@shipments_bp.route("/<shipment_id>/start", methods=["POST", "GET"])
def start_shipment(shipment_id):
    item = find_shipment(shipment_id)

    if not item:
        return {"error": "shipment not found"}, 404

    item.status = "IN_TRANSIT"
    item.departed_at = datetime.utcnow()

    write_audit(
        action="SHIPMENT_IN_TRANSIT",
        object_type="SHIPMENT",
        object_id=item.id,
        user_email="COLLECTOR"
    )

    db.session.commit()

    return {
        "success": True,
        "shipment": item.to_dict()
    }


@shipments_bp.route("/<shipment_id>/arrived", methods=["POST", "GET"])
def arrived_shipment(shipment_id):
    item = find_shipment(shipment_id)

    if not item:
        return {"error": "shipment not found"}, 404

    item.status = "ARRIVED"
    item.arrived_at = datetime.utcnow()

    write_audit(
        action="SHIPMENT_ARRIVED",
        object_type="SHIPMENT",
        object_id=item.id,
        user_email="COLLECTOR"
    )

    db.session.commit()

    return {
        "success": True,
        "shipment": item.to_dict()
    }


@shipments_bp.route("/<shipment_id>/receive", methods=["POST", "GET"])
def receive_shipment(shipment_id):
    data = request.json or {}

    item = find_shipment(shipment_id)

    if not item:
        return {"error": "shipment not found"}, 404

    item.status = "RECEIVED"
    item.received_at = datetime.utcnow()
    item.received_by = data.get("received_by") or "LAB"
    item.receiver_note = data.get("receiver_note")

    write_audit(
        action="LAB_RECEIVED_SHIPMENT",
        object_type="SHIPMENT",
        object_id=item.id,
        user_email=item.received_by
    )

    db.session.commit()

    return {
        "success": True,
        "message": "Shipment received by lab",
        "shipment": item.to_dict()
    }


@shipments_bp.route("/scan/<path:qr_payload>", methods=["GET"])
def scan_qr(qr_payload):
    code = qr_payload.replace("DXCON:SHIPMENT:", "")

    item = Shipment.query.filter_by(
        shipment_code=code
    ).first()

    if not item:
        return {"error": "shipment not found"}, 404

    return {
        "success": True,
        "shipment": item.to_dict()
    }
''',

"app/web/shipments.py": r'''
from flask import Blueprint, request, redirect
from datetime import datetime

from app.extensions.db import db
from app.models.shipment import Shipment
from app.core.audit import write_audit


shipments_web_bp = Blueprint("shipments_web", __name__)


def next_shipment_code():
    count = Shipment.query.count() + 1
    return f"DXCON-SHIP-{datetime.utcnow().strftime('%Y%m%d')}-{count:04d}"


@shipments_web_bp.route("/shipments")
def shipments_page():
    items = Shipment.query.order_by(
        Shipment.created_at.desc()
    ).all()

    rows = ""

    for s in items:
        rows += f"""
        <tr>
            <td>{s.shipment_code}</td>
            <td>{s.status}</td>
            <td>{s.lab_name or ""}</td>
            <td>{s.sample_count or 0}</td>
            <td>{s.temperature or ""}</td>
            <td>{s.received_by or ""}</td>
            <td>{s.received_at or ""}</td>
            <td>
                <a href="/shipments/{s.id}">View</a> |
                <a href="/shipments/{s.id}/qr">QR</a> |
                <a href="/shipments/{s.id}/receive">Lab Receive</a>
            </td>
        </tr>
        """

    return f"""
    <html>
    <body style="font-family:Arial;background:#f1f5f9;padding:30px;">
        <h1>DxCon Shipments</h1>

        <a href="/shipments/new"
           style="background:#0d6efd;color:white;padding:10px 14px;border-radius:6px;text-decoration:none;">
           + New Shipment
        </a>

        <br><br>

        <table border="1" cellpadding="10" style="background:white;width:100%;border-collapse:collapse;">
            <tr>
                <th>Shipment</th>
                <th>Status</th>
                <th>Lab</th>
                <th>Samples</th>
                <th>Temp</th>
                <th>Received By</th>
                <th>Received At</th>
                <th>Action</th>
            </tr>
            {rows}
        </table>

        <br>
        <a href="/monitor">Monitor</a> |
        <a href="/logistics">Logistics</a> |
        <a href="/audit">Audit</a>
    </body>
    </html>
    """


@shipments_web_bp.route("/shipments/new", methods=["GET", "POST"])
def new_shipment():
    if request.method == "POST":
        item = Shipment(
            shipment_code=request.form.get("shipment_code") or next_shipment_code(),
            collector_id=request.form.get("collector_id"),
            transport_box_id=request.form.get("transport_box_id"),
            lab_name=request.form.get("lab_name"),
            sample_count=int(request.form.get("sample_count") or 0),
            temperature=request.form.get("temperature"),
            gps_location=request.form.get("gps_location"),
            status="CREATED"
        )

        db.session.add(item)
        db.session.commit()

        write_audit(
            action="CREATE_SHIPMENT",
            object_type="SHIPMENT",
            object_id=item.id,
            user_email="WEB"
        )
        db.session.commit()

        return redirect("/shipments")

    return """
    <html>
    <body style="font-family:Arial;background:#f1f5f9;padding:30px;">
        <h1>New Shipment</h1>

        <form method="POST">
            <label>Shipment Code</label><br>
            <input name="shipment_code" placeholder="Auto if empty"><br><br>

            <label>Collector ID</label><br>
            <input name="collector_id"><br><br>

            <label>Transport Box ID</label><br>
            <input name="transport_box_id"><br><br>

            <label>Lab / Hospital Name</label><br>
            <input name="lab_name" required><br><br>

            <label>Sample Count</label><br>
            <input name="sample_count" type="number" value="0"><br><br>

            <label>Temperature</label><br>
            <input name="temperature" placeholder="4.2 C"><br><br>

            <label>GPS</label><br>
            <input name="gps_location" placeholder="10.762622,106.660172"><br><br>

            <button type="submit">Create Shipment</button>
        </form>

        <br>
        <a href="/shipments">Back</a>
    </body>
    </html>
    """


@shipments_web_bp.route("/shipments/<shipment_id>")
def shipment_detail(shipment_id):
    s = Shipment.query.get(shipment_id)

    if not s:
        return "Shipment not found", 404

    return f"""
    <html>
    <body style="font-family:Arial;background:#f1f5f9;padding:30px;">
        <h1>Shipment Detail</h1>

        <div style="background:white;padding:20px;border-radius:12px;">
            <p><b>Code:</b> {s.shipment_code}</p>
            <p><b>Status:</b> {s.status}</p>
            <p><b>Lab:</b> {s.lab_name}</p>
            <p><b>Samples:</b> {s.sample_count}</p>
            <p><b>Temperature:</b> {s.temperature}</p>
            <p><b>GPS:</b> {s.gps_location}</p>
            <p><b>QR:</b> {s.qr_payload()}</p>
            <p><b>Received By:</b> {s.received_by or ""}</p>
            <p><b>Received At:</b> {s.received_at or ""}</p>
            <p><b>Note:</b> {s.receiver_note or ""}</p>
        </div>

        <br>
        <a href="/shipments/{s.id}/qr">Show QR</a> |
        <a href="/shipments/{s.id}/receive">Lab Receive</a> |
        <a href="/shipments">Back</a>
    </body>
    </html>
    """


@shipments_web_bp.route("/shipments/<shipment_id>/qr")
def shipment_qr(shipment_id):
    s = Shipment.query.get(shipment_id)

    if not s:
        return "Shipment not found", 404

    return f"""
    <html>
    <body style="font-family:Arial;background:#f1f5f9;padding:30px;text-align:center;">
        <h1>Shipment QR</h1>
        <h2>{s.shipment_code}</h2>

        <div style="font-size:24px;background:white;padding:30px;border-radius:12px;display:inline-block;border:2px dashed #0d6efd;">
            {s.qr_payload()}
        </div>

        <p>Lab app sẽ scan payload này để xác nhận nhận mẫu.</p>

        <br>
        <a href="/shipments/{s.id}/receive">Simulate Lab Receive</a> |
        <a href="/shipments">Back</a>
    </body>
    </html>
    """


@shipments_web_bp.route("/shipments/<shipment_id>/receive", methods=["GET", "POST"])
def lab_receive(shipment_id):
    s = Shipment.query.get(shipment_id)

    if not s:
        return "Shipment not found", 404

    if request.method == "POST":
        s.status = "RECEIVED"
        s.received_at = datetime.utcnow()
        s.received_by = request.form.get("received_by") or "LAB"
        s.receiver_note = request.form.get("receiver_note")

        write_audit(
            action="LAB_RECEIVED_SHIPMENT",
            object_type="SHIPMENT",
            object_id=s.id,
            user_email=s.received_by
        )

        db.session.commit()

        return redirect(f"/shipments/{s.id}")

    return f"""
    <html>
    <body style="font-family:Arial;background:#f1f5f9;padding:30px;">
        <h1>Lab Receive Confirmation</h1>

        <div style="background:white;padding:20px;border-radius:12px;">
            <p><b>Shipment:</b> {s.shipment_code}</p>
            <p><b>Status:</b> {s.status}</p>
            <p><b>Lab:</b> {s.lab_name}</p>
            <p><b>Samples:</b> {s.sample_count}</p>
            <p><b>Temperature:</b> {s.temperature}</p>
            <p><b>QR Payload:</b> {s.qr_payload()}</p>
        </div>

        <br>

        <form method="POST">
            <label>Received By</label><br>
            <input name="received_by" placeholder="Lab staff name"><br><br>

            <label>Note</label><br>
            <textarea name="receiver_note" rows="4" cols="60"></textarea><br><br>

            <button type="submit"
                style="background:#198754;color:white;padding:12px 18px;border:0;border-radius:6px;">
                CONFIRM RECEIVED
            </button>
        </form>

        <br>
        <a href="/shipments">Back</a>
    </body>
    </html>
    """
'''
}

for name, content in files.items():
    path = Path(name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n")
    print("wrote", name)

# models init
models_init = Path("app/models/__init__.py")
if models_init.exists():
    text = models_init.read_text()
    if "from app.models.shipment import Shipment" not in text:
        text += "\nfrom app.models.shipment import Shipment\n"
        models_init.write_text(text)
        print("updated app/models/__init__.py")

# register
init = Path("app/__init__.py")
text = init.read_text()

if "from app.api.shipments.routes import shipments_bp" not in text:
    text = "from app.api.shipments.routes import shipments_bp\n" + text

if "from app.web.shipments import shipments_web_bp" not in text:
    text = "from app.web.shipments import shipments_web_bp\n" + text

if "app.register_blueprint(shipments_bp)" not in text:
    text = text.replace("    return app", "    app.register_blueprint(shipments_bp)\n    return app")

if "app.register_blueprint(shipments_web_bp)" not in text:
    text = text.replace("    return app", "    app.register_blueprint(shipments_web_bp)\n    return app")

init.write_text(text)
print("registered shipment module")
