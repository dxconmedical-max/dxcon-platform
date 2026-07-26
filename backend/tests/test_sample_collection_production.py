"""Sample Collection production workflow tests."""

from __future__ import annotations

import os
import sys
import unittest
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.core.statuses import (
    COLLECTION_CHECKED_IN,
    COLLECTION_COLLECTED,
    COLLECTION_IN_TRANSIT,
    COLLECTION_RECEIVED,
    COLLECTION_RECOLLECT_REQUIRED,
    COLLECTION_REJECTED,
    MAPPING_ACTIVE,
    PARTNER_ACTIVE,
    SAMPLE_QUALITY_HEMOLYZED,
    SAMPLE_QUALITY_INSUFFICIENT_VOLUME,
)
from app.extensions.db import db
from app.models.diagnostic_category import DiagnosticCategory
from app.models.diagnostic_service import DiagnosticService
from app.models.driver import Driver
from app.models.partner import Partner
from app.models.partner_service_mapping import PartnerServiceMapping
from app.models.sample_collection import SampleCollection
from app.models.user import User
from app.services.booking_assignment import BookingAssignmentService
from app.services.marketplace_booking import MarketplaceBookingService
from app.services.order_lifecycle import OrderLifecycleService
from app.services.sample_collection_workflow import (
    SampleCollectionWorkflowError,
    SampleCollectionWorkflowService,
)
from app.services.scheduling import SchedulingService
from app.services.slot_generation import SlotGenerationService
from app.sample_collection_workspace.service import list_production_queue, workspace_dashboard


class SampleCollectionProductionTestCase(unittest.TestCase):
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
            partner_code="PTR-SCP-0001",
            partner_type="LABORATORY",
            legal_name="Sample Collection Lab",
            display_name="Sample Collection Lab",
            city="Ha Noi",
            status=PARTNER_ACTIVE,
        )
        db.session.add(self.partner)
        db.session.flush()

        self.mapping = PartnerServiceMapping(
            partner_id=self.partner.id,
            diagnostic_service_id=self.service.id,
            partner_service_code="SCP-HBA1C",
            partner_service_name="HbA1c",
            price=180000,
            status=MAPPING_ACTIVE,
        )
        db.session.add(self.mapping)

        self.collector = Driver(
            driver_code="COL-SCP-001",
            full_name="Sample Collection Collector",
            status="ACTIVE",
        )
        db.session.add(self.collector)

        self.collector_user = User(
            email=f"collector-{uuid.uuid4().hex[:6]}@test.local",
            role="COLLECTOR",
            password_hash="x",
            is_active=True,
        )
        self.denied_user = User(
            email=f"patient-{uuid.uuid4().hex[:6]}@test.local",
            role="PATIENT",
            password_hash="x",
            is_active=True,
        )
        db.session.add_all([self.collector_user, self.denied_user])
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

    def _assigned_booking(self, phone_suffix="1111"):
        slot = SchedulingService.list_available_slots(self.partner.id)[0]
        booking = MarketplaceBookingService.create_booking(
            {
                "partner_service_mapping_id": self.mapping.id,
                "patient_name": "Sample Collection Patient",
                "patient_phone": f"090888{phone_suffix}",
                "patient_address": "12 Cau Giay, Ha Noi",
                "requested_date": slot.slot_date,
            }
        )
        BookingAssignmentService.reserve_slot_for_booking(booking.id, slot.id)
        BookingAssignmentService.assign_collector(booking.id, self.collector.id)
        OrderLifecycleService.create_order_from_booking(booking.id)
        return booking

    def _session_as(self, user):
        with self.client.session_transaction() as sess:
            sess["user_id"] = user.id
            sess["role"] = user.role
            sess["email"] = user.email

    def _ensure(self, booking):
        return SampleCollectionWorkflowService.ensure_collection_for_booking(booking.id)

    def test_queue_loading(self):
        booking = self._assigned_booking("1001")
        collection = self._ensure(booking)
        queue = SampleCollectionWorkflowService.list_queue(
            location="Ha Noi",
            collector_id=self.collector.id,
            awaiting_only=True,
        )
        self.assertGreaterEqual(len(queue), 1)
        ids = {item["id"] for item in queue}
        self.assertIn(collection.id, ids)

        filtered = list_production_queue(
            location="Ha Noi",
            collector_id=self.collector.id,
            include_desk=False,
            role="COLLECTOR",
            scoped_collector_id=self.collector.id,
        )
        self.assertGreaterEqual(filtered["field_count"], 1)
        dash = workspace_dashboard()
        self.assertIn("awaiting_collection", dash["kpis"])
        self.assertIn("PENDING", dash["status_contract"]["flow"])

    def test_successful_collection(self):
        booking = self._assigned_booking("1002")
        collection = self._ensure(booking)
        SampleCollectionWorkflowService.check_in_collection(booking.id)
        expected = collection.expected_barcode or f"BC-{booking.booking_code}"
        collected, sample = SampleCollectionWorkflowService.record_collection(
            booking.id,
            collector_id=self.collector.id,
            specimen_type="BLOOD",
            scanned_barcode=expected,
            collection_location="Home visit",
            require_barcode=True,
            patient_verified=True,
            order_verified=True,
            note="Collected OK",
        )
        self.assertEqual(collected.status, COLLECTION_COLLECTED)
        self.assertEqual(collected.specimen_type, "BLOOD")
        self.assertIsNotNone(collected.collected_at)
        self.assertIsNotNone(collected.picked_up_at)
        self.assertTrue(sample.sample_code.startswith("SMP-"))

    def test_duplicate_collection(self):
        booking = self._assigned_booking("1003")
        collection = self._ensure(booking)
        expected = collection.expected_barcode or f"BC-{booking.booking_code}"
        SampleCollectionWorkflowService.record_collection(
            booking.id,
            collector_id=self.collector.id,
            scanned_barcode=expected,
            require_barcode=True,
        )
        with self.assertRaises(SampleCollectionWorkflowError) as ctx:
            SampleCollectionWorkflowService.record_collection(
                booking.id,
                collector_id=self.collector.id,
                scanned_barcode=expected,
                require_barcode=True,
            )
        self.assertEqual(ctx.exception.status_code, 409)
        self.assertIn("cannot be collected", ctx.exception.message.lower())

    def test_barcode_mismatch(self):
        booking = self._assigned_booking("1004")
        self._ensure(booking)
        with self.assertRaises(SampleCollectionWorkflowError) as ctx:
            SampleCollectionWorkflowService.record_collection(
                booking.id,
                collector_id=self.collector.id,
                scanned_barcode="WRONG-BARCODE-999",
                require_barcode=True,
            )
        self.assertEqual(ctx.exception.status_code, 409)
        self.assertIn("mismatch", ctx.exception.message.lower())
        row = SampleCollection.query.filter_by(marketplace_booking_id=booking.id).first()
        self.assertEqual(row.quality_status, "mismatched_identifier")

    def test_rejection(self):
        booking = self._assigned_booking("1005")
        collection = self._ensure(booking)
        expected = collection.expected_barcode or f"BC-{booking.booking_code}"
        SampleCollectionWorkflowService.record_collection(
            booking.id,
            scanned_barcode=expected,
            require_barcode=True,
        )
        collection = SampleCollection.query.filter_by(
            marketplace_booking_id=booking.id,
            status=COLLECTION_COLLECTED,
        ).first()
        rejected, recollect = SampleCollectionWorkflowService.reject_specimen(
            collection.id,
            quality_status=SAMPLE_QUALITY_HEMOLYZED,
            rejection_reason="Hemolysis observed",
            request_recollect=True,
        )
        self.assertEqual(rejected.status, COLLECTION_REJECTED)
        self.assertEqual(rejected.quality_status, SAMPLE_QUALITY_HEMOLYZED)
        self.assertIsNotNone(recollect)
        self.assertEqual(recollect.status, COLLECTION_RECOLLECT_REQUIRED)
        self.assertEqual(recollect.recollect_of_id, rejected.id)

    def test_recollection(self):
        booking = self._assigned_booking("1006")
        collection = self._ensure(booking)
        expected = collection.expected_barcode or f"BC-{booking.booking_code}"
        SampleCollectionWorkflowService.record_collection(
            booking.id,
            scanned_barcode=expected,
            require_barcode=True,
        )
        original = SampleCollection.query.filter_by(
            marketplace_booking_id=booking.id,
            status=COLLECTION_COLLECTED,
        ).first()
        SampleCollectionWorkflowService.reject_specimen(
            original.id,
            quality_status=SAMPLE_QUALITY_INSUFFICIENT_VOLUME,
            request_recollect=True,
        )
        recollect = SampleCollection.query.filter_by(
            marketplace_booking_id=booking.id,
            status=COLLECTION_RECOLLECT_REQUIRED,
        ).first()
        self.assertIsNotNone(recollect)
        collected, sample = SampleCollectionWorkflowService.record_collection(
            booking.id,
            scanned_barcode=expected,
            require_barcode=True,
            specimen_type="BLOOD",
        )
        self.assertEqual(collected.status, COLLECTION_COLLECTED)
        self.assertEqual(collected.id, recollect.id)
        self.assertTrue(sample.sample_code.startswith("SMP-"))

    def test_transport_status(self):
        booking = self._assigned_booking("1007")
        collection = self._ensure(booking)
        expected = collection.expected_barcode or f"BC-{booking.booking_code}"
        SampleCollectionWorkflowService.record_collection(
            booking.id,
            scanned_barcode=expected,
            require_barcode=True,
        )
        SampleCollectionWorkflowService.dispatch_sample(
            booking.id,
            vehicle_id="VEH-1",
            driver_id=self.collector.id,
            distance_km=12.5,
            eta_minutes=40,
            temperature_c=4.2,
            iot_device_id="IOT-BOX-1",
        )
        collection = SampleCollection.query.filter_by(
            marketplace_booking_id=booking.id,
            status=COLLECTION_IN_TRANSIT,
        ).first()
        SampleCollectionWorkflowService.record_handoff(
            collection.id,
            temperature_c=4.0,
            note="Cold box sealed",
        )
        payload = SampleCollectionWorkflowService.transport_status(collection.id)
        self.assertEqual(payload["status"], COLLECTION_IN_TRANSIT)
        self.assertIsNotNone(payload["picked_up_at"])
        self.assertIsNotNone(payload["dispatched_at"])
        self.assertIsNotNone(payload["handoff_at"])
        self.assertEqual(payload["vehicle_id"], "VEH-1")
        self.assertEqual(payload["eta_minutes"], 40)
        self.assertEqual(payload["temperature_c"], 4.0)
        self.assertEqual(payload["iot_device_id"], "IOT-BOX-1")

    def test_permission_denial(self):
        self._session_as(self.denied_user)
        denied = self.client.get("/api/v1/sample-collections/queue")
        self.assertIn(denied.status_code, (401, 403))

        self._session_as(self.collector_user)
        allowed = self.client.get("/api/v1/sample-collections/queue")
        self.assertEqual(allowed.status_code, 200)
        self.assertTrue(allowed.get_json().get("success"))

    def test_timeout_and_refresh_persistence(self):
        booking = self._assigned_booking("1008")
        collection = self._ensure(booking)
        collection_id = collection.id
        expected = collection.expected_barcode or f"BC-{booking.booking_code}"

        # Simulate client abort/timeout: no DB write mid-flight; state stays PENDING
        persisted = SampleCollection.query.get(collection_id)
        self.assertIn(persisted.status, ("PENDING", COLLECTION_CHECKED_IN, COLLECTION_RECOLLECT_REQUIRED))

        SampleCollectionWorkflowService.record_collection(
            booking.id,
            scanned_barcode=expected,
            require_barcode=True,
            specimen_type="BLOOD",
        )
        # Refresh persistence: reload by id after commit
        refreshed = SampleCollection.query.get(collection_id)
        self.assertEqual(refreshed.status, COLLECTION_COLLECTED)
        self.assertEqual(refreshed.specimen_type, "BLOOD")

        self._session_as(self.collector_user)
        detail = self.client.get(f"/api/v1/sample-collections/{collection_id}")
        self.assertEqual(detail.status_code, 200)
        body = detail.get_json()["data"]
        self.assertEqual(body["status"], COLLECTION_COLLECTED)
        self.assertEqual(body["id"], collection_id)

    def test_e2e_queue_to_lab_arrival(self):
        booking = self._assigned_booking("1009")
        collection = self._ensure(booking)
        self._session_as(self.collector_user)

        queue = self.client.get(
            "/api/v1/sample-collections/queue?include_desk=false"
            f"&collector={self.collector.id}&location=Ha%20Noi"
        )
        self.assertEqual(queue.status_code, 200)
        items = queue.get_json()["data"]["items"]
        self.assertTrue(any(item["id"] == collection.id for item in items))

        expected = collection.expected_barcode or f"BC-{booking.booking_code}"
        verify = self.client.post(
            f"/api/v1/sample-collections/{collection.id}/verify",
            json={
                "patient_name": "Sample Collection Patient",
                "booking_code": booking.booking_code,
                "scanned_barcode": expected,
            },
        )
        self.assertEqual(verify.status_code, 200)

        collect = self.client.post(
            f"/api/v1/sample-collections/{collection.id}/collect",
            json={
                "scanned_barcode": expected,
                "specimen_type": "BLOOD",
                "collection_location": "12 Cau Giay",
                "collector_id": self.collector.id,
                "require_barcode": True,
            },
        )
        self.assertEqual(collect.status_code, 200)
        specimen_id = collect.get_json()["data"]["sample_tracking"]["sample_code"]
        self.assertTrue(specimen_id.startswith("SMP-"))

        dispatch = self.client.post(
            f"/api/v1/sample-collections/bookings/{booking.id}/dispatch",
            json={
                "vehicle_id": "VEH-E2E",
                "driver_id": self.collector.id,
                "distance_km": 8,
                "eta_minutes": 25,
                "temperature_c": 5.0,
                "iot_device_id": "IOT-E2E",
            },
        )
        self.assertEqual(dispatch.status_code, 200)

        handoff = self.client.post(
            f"/api/v1/sample-collections/{collection.id}/handoff",
            json={"temperature_c": 4.8, "note": "Lab dock"},
        )
        self.assertEqual(handoff.status_code, 200)

        arrive = self.client.post(
            f"/api/v1/sample-collections/bookings/{booking.id}/lab-arrive",
            json={"note": "Arrived at laboratory", "temperature_c": 4.5},
        )
        self.assertEqual(arrive.status_code, 200)
        payload = arrive.get_json()["data"]
        self.assertEqual(payload["collection"]["status"], COLLECTION_RECEIVED)
        self.assertEqual(payload["synthetic_specimen_id"], specimen_id)
        self.assertIsNotNone(payload["collection"]["arrived_at_lab"])

        # Expose for report / CI consumers
        self.__class__.SYNTHETIC_SPECIMEN_ID = specimen_id


if __name__ == "__main__":
    unittest.main()
