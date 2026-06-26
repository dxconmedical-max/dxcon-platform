import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from app.models.audit_log import AuditLog
from app.models.event_log import EventLog
from app.models.shipment import Shipment
from app.models.shipment_timeline import ShipmentTimeline
from app.models.transport_box import TransportBox
from app.core.statuses import (
    BOX_IN_TRANSIT,
    BOX_IN_USE,
    BOX_ONLINE,
    SHIPMENT_ACCEPTED,
    SHIPMENT_CREATED,
    SHIPMENT_IN_TRANSIT,
)


class CollectorWorkflowV1TestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

        self.collector_id = "collector-001"
        self.box = TransportBox(
            box_code="BOX-FP003-001",
            status=BOX_ONLINE,
        )
        db.session.add(self.box)
        db.session.flush()

        self.shipment = Shipment(
            shipment_code="DXCON-SHIP-FP003-001",
            transport_box_id=self.box.id,
            lab_name="DxCon Lab",
            status=SHIPMENT_CREATED,
        )
        db.session.add(self.shipment)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_accept_shipment_updates_status_box_and_logs(self):
        response = self.client.post(
            f"/api/v1/collector/shipments/{self.shipment.id}/accept",
            json={
                "collector_id": self.collector_id,
                "latitude": "10.1",
                "longitude": "106.2",
                "actor": "collector@dxcon.com",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload["success"])
        self.assertEqual(payload["shipment"]["status"], SHIPMENT_ACCEPTED)
        self.assertEqual(payload["shipment"]["collector_id"], self.collector_id)
        self.assertEqual(payload["shipment"]["gps_location"], "10.1,106.2")

        box = TransportBox.query.get(self.box.id)
        self.assertEqual(box.status, BOX_IN_USE)

        self.assertEqual(
            AuditLog.query.filter_by(action="COLLECTOR_ACCEPT_SHIPMENT").count(),
            1,
        )
        self.assertEqual(
            ShipmentTimeline.query.filter_by(event_type="COLLECTOR_ACCEPTED").count(),
            1,
        )
        self.assertEqual(
            EventLog.query.filter_by(event_type="COLLECTOR_ACCEPTED_SHIPMENT").count(),
            1,
        )

    def test_start_trip_requires_accepted_status(self):
        response = self.client.post(
            f"/api/v1/collector/shipments/{self.shipment.id}/start-trip",
            json={"collector_id": self.collector_id},
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("ACCEPTED", response.get_json()["error"])

    def test_accept_then_start_trip(self):
        accept = self.client.post(
            f"/api/v1/collector/shipments/{self.shipment.id}/accept",
            json={"collector_id": self.collector_id},
        )
        self.assertEqual(accept.status_code, 200)

        start = self.client.post(
            f"/api/v1/collector/shipments/{self.shipment.id}/start-trip",
            json={"collector_id": self.collector_id},
        )

        self.assertEqual(start.status_code, 200)
        payload = start.get_json()
        self.assertEqual(payload["shipment"]["status"], SHIPMENT_IN_TRANSIT)
        self.assertIsNotNone(payload["shipment"]["departed_at"])

        box = TransportBox.query.get(self.box.id)
        self.assertEqual(box.status, BOX_IN_TRANSIT)

        self.assertEqual(
            AuditLog.query.filter_by(action="COLLECTOR_START_TRIP").count(),
            1,
        )
        self.assertEqual(
            ShipmentTimeline.query.filter_by(event_type="TRIP_STARTED").count(),
            1,
        )
        self.assertEqual(
            EventLog.query.filter_by(event_type="SHIPMENT_TRIP_STARTED").count(),
            1,
        )

    def test_legacy_start_endpoint(self):
        response = self.client.post(
            f"/api/v1/shipments/{self.shipment.id}/start",
            json={"collector_id": self.collector_id},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload["success"])
        self.assertEqual(payload["shipment"]["status"], SHIPMENT_IN_TRANSIT)

    def test_list_collector_shipments(self):
        response = self.client.get("/api/v1/collector/shipments")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["count"], 1)
        self.assertEqual(payload["shipments"][0]["shipment_code"], self.shipment.shipment_code)


if __name__ == "__main__":
    unittest.main()
