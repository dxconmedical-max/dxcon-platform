import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.core.statuses import (
    ASSIGNMENT_ACCEPTED,
    ASSIGNMENT_ASSIGNED,
    COLLECTOR_OPS_ON_DUTY,
    MAPPING_ACTIVE,
    PARTNER_ACTIVE,
    ROUTE_IN_PROGRESS,
    ROUTE_OPTIMIZED,
    SHIPMENT_CREATED,
    VEHICLE_ACTIVE,
)
from app.extensions.db import db
from app.models.booking_assignment import BookingAssignment
from app.models.collector_operation_timeline import CollectorOperationTimeline
from app.models.collector_route import CollectorRoute
from app.models.collector_vehicle import CollectorVehicle
from app.models.diagnostic_category import DiagnosticCategory
from app.models.diagnostic_service import DiagnosticService
from app.models.driver import Driver
from app.models.partner import Partner
from app.models.partner_service_mapping import PartnerServiceMapping
from app.models.shipment import Shipment
from app.models.transport_box import TransportBox
from app.services.booking_assignment import BookingAssignmentService
from app.services.collector_operations import CollectorOperationsService
from app.services.marketplace_booking import MarketplaceBookingService
from app.services.order_lifecycle import OrderLifecycleService
from app.services.scheduling import SchedulingService
from app.services.slot_generation import SlotGenerationService


class CollectorOperationsTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

        self.category = DiagnosticCategory(
            category_code="BIOCHEM",
            name="Biochemistry",
            is_active=True,
        )
        db.session.add(self.category)
        db.session.flush()

        self.service = DiagnosticService(
            service_code="HBA1C",
            name="HbA1c",
            category_id=self.category.id,
            estimated_turnaround_hours=24,
            is_active=True,
        )
        db.session.add(self.service)

        self.partner = Partner(
            partner_code="PTR-COP-0001",
            partner_type="LABORATORY",
            legal_name="Collector Ops Lab",
            display_name="Collector Ops Lab",
            city="Ha Noi",
            status=PARTNER_ACTIVE,
        )
        db.session.add(self.partner)
        db.session.flush()

        self.mapping = PartnerServiceMapping(
            partner_id=self.partner.id,
            diagnostic_service_id=self.service.id,
            partner_service_code="COP-HBA1C",
            partner_service_name="HbA1c",
            price=180000,
            status=MAPPING_ACTIVE,
        )
        db.session.add(self.mapping)

        self.collector = Driver(
            driver_code="COL-COP-001",
            full_name="Collector Ops User",
            phone="0909111000",
            status="ACTIVE",
        )
        db.session.add(self.collector)

        self.box = TransportBox(box_code="BOX-COP-001", status="ONLINE")
        db.session.add(self.box)
        db.session.commit()

        SlotGenerationService.generate_partner_daily_slots(self.partner.id, days=2)
        SlotGenerationService.generate_collector_availability(
            self.collector.id,
            days=2,
            city="Ha Noi",
            district="Cau Giay",
        )

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _assigned_booking(self):
        slot = SchedulingService.list_available_slots(self.partner.id)[0]
        booking = MarketplaceBookingService.create_booking(
            {
                "partner_service_mapping_id": self.mapping.id,
                "patient_name": "Collector Ops Patient",
                "patient_phone": "0909222000",
                "requested_date": slot.slot_date,
            }
        )
        BookingAssignmentService.reserve_slot_for_booking(booking.id, slot.id)
        assignment = BookingAssignmentService.assign_collector(booking.id, self.collector.id)
        OrderLifecycleService.create_order_from_booking(booking.id)
        return booking, assignment

    def test_profile_and_vehicle_management(self):
        response = self.client.put(
            f"/api/v1/collector-operations/collectors/{self.collector.id}/profile",
            json={"email": "collector@dxcon.com", "home_city": "Ha Noi"},
        )
        self.assertEqual(response.status_code, 200)

        vehicle_response = self.client.post(
            f"/api/v1/collector-operations/collectors/{self.collector.id}/vehicles",
            json={"plate_number": "51A-99999", "vehicle_type": "MOTORBIKE"},
        )
        self.assertEqual(vehicle_response.status_code, 201)
        vehicle = vehicle_response.get_json()["vehicle"]

        assign_response = self.client.post(
            f"/api/v1/collector-operations/collectors/{self.collector.id}/vehicles/{vehicle['id']}/assign"
        )
        self.assertEqual(assign_response.status_code, 200)
        self.assertEqual(assign_response.get_json()["collector"]["active_vehicle_id"], vehicle["id"])

    def test_assignment_route_and_pickup_workflow(self):
        booking, assignment = self._assigned_booking()

        accept = self.client.post(
            f"/api/v1/collector-operations/assignments/{assignment.id}/accept",
            json={"collector_id": self.collector.id},
        )
        self.assertEqual(accept.status_code, 200)
        self.assertEqual(
            accept.get_json()["assignment"]["assignment_status"],
            ASSIGNMENT_ACCEPTED,
        )

        route_response = self.client.post(
            f"/api/v1/collector-operations/collectors/{self.collector.id}/routes",
            json={"transport_box_id": self.box.id},
        )
        self.assertEqual(route_response.status_code, 201)
        route = route_response.get_json()["route"]

        optimize = self.client.post(
            f"/api/v1/collector-operations/routes/{route['id']}/optimize"
        )
        self.assertEqual(optimize.status_code, 200)
        self.assertEqual(optimize.get_json()["route"]["status"], ROUTE_OPTIMIZED)

        start = self.client.post(
            f"/api/v1/collector-operations/routes/{route['id']}/start",
            json={"latitude": "21.0285", "longitude": "105.8542"},
        )
        self.assertEqual(start.status_code, 200)
        self.assertEqual(start.get_json()["route"]["status"], ROUTE_IN_PROGRESS)

        check_in = self.client.post(
            f"/api/v1/collector-operations/collectors/{self.collector.id}/check-in",
            json={"booking_id": booking.id, "latitude": "21.0285", "longitude": "105.8542"},
        )
        self.assertEqual(check_in.status_code, 200)

        pickup = self.client.post(
            f"/api/v1/collector-operations/bookings/{booking.id}/pickup",
            json={
                "collector_id": self.collector.id,
                "latitude": "21.0285",
                "longitude": "105.8542",
            },
        )
        self.assertEqual(pickup.status_code, 200)

        gps = self.client.post(
            f"/api/v1/collector-operations/collectors/{self.collector.id}/gps",
            json={
                "latitude": "21.0290",
                "longitude": "105.8550",
                "route_id": route["id"],
            },
        )
        self.assertEqual(gps.status_code, 200)

        timeline = CollectorOperationTimeline.query.filter_by(
            collector_id=self.collector.id
        ).count()
        self.assertGreater(timeline, 0)

    def test_qr_handover_proof_offline_and_dashboards(self):
        booking, assignment = self._assigned_booking()
        CollectorOperationsService.accept_assignment(assignment.id, self.collector.id)
        collection, sample = CollectorOperationsService.pickup_sample(
            booking.id,
            self.collector.id,
        )

        qr = self.client.post(
            "/api/v1/collector-operations/qr/scan",
            json={
                "qr_payload": f"DXCON:SAMPLE:{sample.sample_code}",
                "collector_id": self.collector.id,
            },
        )
        self.assertEqual(qr.status_code, 200)
        self.assertEqual(qr.get_json()["type"], "SAMPLE")

        handover = self.client.post(
            "/api/v1/collector-operations/handovers",
            json={
                "collector_id": self.collector.id,
                "handover_type": "SAMPLE",
                "object_code": sample.sample_code,
                "booking_id": booking.id,
            },
        )
        self.assertEqual(handover.status_code, 201)

        proof = self.client.post(
            "/api/v1/collector-operations/proofs",
            json={
                "collector_id": self.collector.id,
                "proof_type": "PHOTO",
                "booking_id": booking.id,
                "file_name": "pickup.jpg",
                "content_base64": "base64-photo-data",
            },
        )
        self.assertEqual(proof.status_code, 201)

        signature = self.client.post(
            "/api/v1/collector-operations/proofs",
            json={
                "collector_id": self.collector.id,
                "proof_type": "SIGNATURE",
                "booking_id": booking.id,
                "signer_name": "Patient Name",
                "content_base64": "base64-signature-data",
            },
        )
        self.assertEqual(signature.status_code, 201)

        offline = self.client.post(
            f"/api/v1/collector-operations/collectors/{self.collector.id}/offline/events",
            json={
                "client_event_id": "offline-gps-001",
                "event_type": "GPS",
                "payload": {"latitude": "21.03", "longitude": "105.86"},
            },
        )
        self.assertEqual(offline.status_code, 201)

        sync = self.client.post(
            f"/api/v1/collector-operations/collectors/{self.collector.id}/offline/sync"
        )
        self.assertEqual(sync.status_code, 200)
        self.assertGreaterEqual(sync.get_json()["summary"]["synced"], 1)

        dashboard = self.client.get(
            f"/api/v1/collector-operations/collectors/{self.collector.id}/dashboard"
        )
        self.assertEqual(dashboard.status_code, 200)
        self.assertEqual(dashboard.get_json()["collector"]["id"], self.collector.id)

        supervisor = self.client.get("/api/v1/collector-operations/supervisor/dashboard")
        self.assertEqual(supervisor.status_code, 200)
        self.assertIn("collectors_total", supervisor.get_json())

    def test_shipment_accept_and_routes_registered(self):
        shipment = Shipment(
            shipment_code="DXCON-SHIP-COP-001",
            transport_box_id=self.box.id,
            status=SHIPMENT_CREATED,
        )
        db.session.add(shipment)
        db.session.commit()

        accept = self.client.post(
            f"/api/v1/collector-operations/shipments/{shipment.id}/accept",
            json={"collector_id": self.collector.id},
        )
        self.assertEqual(accept.status_code, 200)

        start = self.client.post(
            f"/api/v1/collector-operations/shipments/{shipment.id}/start-trip",
            json={"collector_id": self.collector.id},
        )
        self.assertEqual(start.status_code, 200)

        routes = {str(rule) for rule in self.app.url_map.iter_rules()}
        self.assertIn("/api/v1/collector-operations/supervisor/dashboard", routes)
        self.assertIn("/collector-operations", routes)
        self.assertIn("/collector-operations/supervisor", routes)


if __name__ == "__main__":
    unittest.main()
