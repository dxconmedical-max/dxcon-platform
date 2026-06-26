from pathlib import Path

files = {
"app/models/shipment_item.py": r'''
from app.extensions.db import db
from datetime import datetime
import uuid


class ShipmentItem(db.Model):
    __tablename__ = "shipment_items"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    shipment_id = db.Column(db.String(36), nullable=False)
    order_id = db.Column(db.String(36))
    order_item_id = db.Column(db.String(36))
    sample_tracking_id = db.Column(db.String(36))

    sample_code = db.Column(db.String(100))
    tube_type = db.Column(db.String(100))
    test_name = db.Column(db.String(255))

    status = db.Column(db.String(50), default="CREATED")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def qr_payload(self):
        return f"DXCON:SAMPLE:{self.sample_code or self.id}"

    def to_dict(self):
        return {
            "id": self.id,
            "shipment_id": self.shipment_id,
            "order_id": self.order_id,
            "order_item_id": self.order_item_id,
            "sample_tracking_id": self.sample_tracking_id,
            "sample_code": self.sample_code,
            "tube_type": self.tube_type,
            "test_name": self.test_name,
            "status": self.status,
            "qr_payload": self.qr_payload(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
''',

"app/models/shipment_timeline.py": r'''
from app.extensions.db import db
from datetime import datetime
import uuid


class ShipmentTimeline(db.Model):
    __tablename__ = "shipment_timelines"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    shipment_id = db.Column(db.String(36), nullable=False)
    event_type = db.Column(db.String(100), nullable=False)
    note = db.Column(db.Text)
    actor = db.Column(db.String(255))
    gps_location = db.Column(db.String(255))
    temperature = db.Column(db.String(50))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "shipment_id": self.shipment_id,
            "event_type": self.event_type,
            "note": self.note,
            "actor": self.actor,
            "gps_location": self.gps_location,
            "temperature": self.temperature,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
''',

"app/models/event_log.py": r'''
from app.extensions.db import db
from datetime import datetime
import uuid


class EventLog(db.Model):
    __tablename__ = "event_logs"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    event_type = db.Column(db.String(100), nullable=False)
    object_type = db.Column(db.String(100))
    object_id = db.Column(db.String(100))
    message = db.Column(db.Text)
    severity = db.Column(db.String(50), default="INFO")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "event_type": self.event_type,
            "object_type": self.object_type,
            "object_id": self.object_id,
            "message": self.message,
            "severity": self.severity,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
''',

"app/core/events.py": r'''
from app.extensions.db import db
from app.models.event_log import EventLog


def write_event(
    event_type,
    object_type=None,
    object_id=None,
    message=None,
    severity="INFO"
):
    item = EventLog(
        event_type=event_type,
        object_type=object_type,
        object_id=str(object_id) if object_id else None,
        message=message,
        severity=severity
    )

    db.session.add(item)
    return item
''',

"app/core/qr_service.py": r'''
def shipment_qr_payload(shipment_code):
    return f"DXCON:SHIPMENT:{shipment_code}"


def sample_qr_payload(sample_code):
    return f"DXCON:SAMPLE:{sample_code}"


def box_qr_payload(box_code):
    return f"DXCON:BOX:{box_code}"


def parse_qr_payload(payload):
    parts = payload.split(":")

    if len(parts) != 3:
        return {
            "valid": False,
            "type": None,
            "code": None
        }

    namespace, object_type, code = parts

    if namespace != "DXCON":
        return {
            "valid": False,
            "type": None,
            "code": None
        }

    return {
        "valid": True,
        "type": object_type,
        "code": code
    }
''',

"app/api/logistics_v2/routes.py": r'''
from flask import Blueprint, request

from app.extensions.db import db
from app.models.shipment import Shipment
from app.models.shipment_item import ShipmentItem
from app.models.shipment_timeline import ShipmentTimeline
from app.models.event_log import EventLog
from app.core.events import write_event
from app.core.audit import write_audit
from app.core.qr_service import parse_qr_payload


logistics_v2_bp = Blueprint(
    "logistics_v2",
    __name__,
    url_prefix="/api/v1/logistics-v2"
)


@logistics_v2_bp.route("/shipments/<shipment_id>/items")
def shipment_items(shipment_id):
    items = ShipmentItem.query.filter_by(
        shipment_id=shipment_id
    ).all()

    return {
        "count": len(items),
        "items": [x.to_dict() for x in items]
    }


@logistics_v2_bp.route("/shipments/<shipment_id>/items", methods=["POST"])
def add_shipment_item(shipment_id):
    data = request.json or {}

    item = ShipmentItem(
        shipment_id=shipment_id,
        order_id=data.get("order_id"),
        order_item_id=data.get("order_item_id"),
        sample_tracking_id=data.get("sample_tracking_id"),
        sample_code=data.get("sample_code"),
        tube_type=data.get("tube_type"),
        test_name=data.get("test_name"),
        status=data.get("status") or "CREATED"
    )

    db.session.add(item)

    write_event(
        event_type="SHIPMENT_ITEM_ADDED",
        object_type="SHIPMENT",
        object_id=shipment_id,
        message=f"Sample added: {item.sample_code}"
    )

    db.session.commit()

    return {
        "success": True,
        "item": item.to_dict()
    }, 201


@logistics_v2_bp.route("/shipments/<shipment_id>/timeline")
def shipment_timeline(shipment_id):
    items = ShipmentTimeline.query.filter_by(
        shipment_id=shipment_id
    ).order_by(
        ShipmentTimeline.created_at.asc()
    ).all()

    return {
        "count": len(items),
        "timeline": [x.to_dict() for x in items]
    }


@logistics_v2_bp.route("/shipments/<shipment_id>/timeline", methods=["POST"])
def add_timeline_event(shipment_id):
    data = request.json or {}

    item = ShipmentTimeline(
        shipment_id=shipment_id,
        event_type=data.get("event_type") or "EVENT",
        note=data.get("note"),
        actor=data.get("actor"),
        gps_location=data.get("gps_location"),
        temperature=data.get("temperature")
    )

    db.session.add(item)

    write_event(
        event_type=item.event_type,
        object_type="SHIPMENT",
        object_id=shipment_id,
        message=item.note
    )

    db.session.commit()

    return {
        "success": True,
        "timeline": item.to_dict()
    }, 201


@logistics_v2_bp.route("/scan", methods=["POST"])
def scan_qr():
    data = request.json or {}
    payload = data.get("payload") or ""

    parsed = parse_qr_payload(payload)

    if not parsed["valid"]:
        return {
            "success": False,
            "error": "invalid QR payload"
        }, 400

    object_type = parsed["type"]
    code = parsed["code"]

    if object_type == "SHIPMENT":
        shipment = Shipment.query.filter_by(
            shipment_code=code
        ).first()

        if not shipment:
            return {"success": False, "error": "shipment not found"}, 404

        return {
            "success": True,
            "type": "SHIPMENT",
            "shipment": shipment.to_dict()
        }

    if object_type == "SAMPLE":
        item = ShipmentItem.query.filter_by(
            sample_code=code
        ).first()

        if not item:
            return {"success": False, "error": "sample not found"}, 404

        return {
            "success": True,
            "type": "SAMPLE",
            "item": item.to_dict()
        }

    return {
        "success": False,
        "error": "unsupported QR type"
    }, 400


@logistics_v2_bp.route("/events")
def events():
    items = EventLog.query.order_by(
        EventLog.created_at.desc()
    ).limit(200).all()

    return {
        "count": len(items),
        "events": [x.to_dict() for x in items]
    }
''',

"app/web/logistics_v2.py": r'''
from flask import Blueprint
from app.models.shipment import Shipment
from app.models.shipment_item import ShipmentItem
from app.models.shipment_timeline import ShipmentTimeline
from app.models.event_log import EventLog


logistics_v2_web_bp = Blueprint(
    "logistics_v2_web",
    __name__
)


@logistics_v2_web_bp.route("/logistics-v2")
def logistics_v2_dashboard():
    shipment_count = Shipment.query.count()
    item_count = ShipmentItem.query.count()
    event_count = EventLog.query.count()

    waiting_receive = Shipment.query.filter(
        Shipment.status.in_(["IN_TRANSIT", "ARRIVED"])
    ).count()

    received = Shipment.query.filter_by(
        status="RECEIVED"
    ).count()

    recent_events = EventLog.query.order_by(
        EventLog.created_at.desc()
    ).limit(20).all()

    event_rows = ""

    for e in recent_events:
        event_rows += f"""
        <tr>
            <td>{e.created_at}</td>
            <td>{e.event_type}</td>
            <td>{e.object_type or ""}</td>
            <td>{e.message or ""}</td>
            <td>{e.severity}</td>
        </tr>
        """

    return f"""
    <html>
    <body style="font-family:Arial;background:#f1f5f9;padding:30px;">
        <h1>DxCon Logistics V2</h1>

        <div style="display:flex;gap:15px;flex-wrap:wrap;">
            <div class="card"><h3>Shipments</h3><h1>{shipment_count}</h1></div>
            <div class="card"><h3>Items</h3><h1>{item_count}</h1></div>
            <div class="card"><h3>Waiting Receive</h3><h1>{waiting_receive}</h1></div>
            <div class="card"><h3>Received</h3><h1>{received}</h1></div>
            <div class="card"><h3>Events</h3><h1>{event_count}</h1></div>
        </div>

        <br>

        <div style="background:white;padding:20px;border-radius:12px;">
            <h2>Recent Logistics Events</h2>
            <table border="1" cellpadding="8" style="width:100%;border-collapse:collapse;">
                <tr>
                    <th>Time</th>
                    <th>Event</th>
                    <th>Object</th>
                    <th>Message</th>
                    <th>Severity</th>
                </tr>
                {event_rows}
            </table>
        </div>

        <br>
        <a href="/shipments">Shipments</a> |
        <a href="/monitor">Monitor</a> |
        <a href="/audit">Audit</a>

        <style>
            .card {{
                background:white;
                padding:20px;
                border-radius:12px;
                width:190px;
                box-shadow:0 4px 12px rgba(0,0,0,.08);
            }}
        </style>
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

models_init = Path("app/models/__init__.py")
text = models_init.read_text()

for line in [
    "from app.models.shipment_item import ShipmentItem",
    "from app.models.shipment_timeline import ShipmentTimeline",
    "from app.models.event_log import EventLog",
]:
    if line not in text:
        text += "\n" + line + "\n"

models_init.write_text(text)

init = Path("app/__init__.py")
text = init.read_text()

imports = [
    "from app.api.logistics_v2.routes import logistics_v2_bp\n",
    "from app.web.logistics_v2 import logistics_v2_web_bp\n",
]

for imp in imports:
    if imp not in text:
        text = imp + text

registers = [
    "    app.register_blueprint(logistics_v2_bp)\n",
    "    app.register_blueprint(logistics_v2_web_bp)\n",
]

for reg in registers:
    if reg.strip() not in text:
        text = text.replace("    return app", reg + "    return app")

init.write_text(text)

print("Logistics Foundation V2 installed")
