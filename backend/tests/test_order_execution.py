import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.core.statuses import (
    MEDICAL_ORDER_BOOKED,
    MEDICAL_ORDER_CANCELLED,
    MEDICAL_ORDER_COLLECTOR_ASSIGNED,
    MEDICAL_ORDER_COLLECTOR_EN_ROUTE,
    MEDICAL_ORDER_ARRIVED,
    MEDICAL_ORDER_COMPLETED,
    MEDICAL_ORDER_CONFIRMED,
    MEDICAL_ORDER_PAID,
    MEDICAL_ORDER_PAYMENT_PENDING,
    MEDICAL_ORDER_RECOLLECT_REQUIRED,
    MEDICAL_ORDER_REFUNDED,
    MEDICAL_ORDER_SAMPLE_COLLECTED,
    MAPPING_ACTIVE,
    PARTNER_ACTIVE,
)
from app.extensions.db import db
from app.models.medical_order import MedicalOrder
from app.models.medical_order_event import MedicalOrderEvent
from app.models.sample_incident import SampleIncident
from app.models.sample_label import SampleLabel
from app.services.booking_assignment import BookingAssignmentService
from app.services.marketplace_booking import MarketplaceBookingService
from app.services.order_lifecycle import OrderLifecycleService
from app.services.order_workflow_service import OrderWorkflowService
from app.services.scheduling import SchedulingService
from app.services.slot_generation import SlotGenerationService
from app.models.diagnostic_category import DiagnosticCategory
from app.models.diagnostic_service import DiagnosticService
from app.models.driver import Driver
from app.models.partner import Partner
from app.models.partner_service_mapping import PartnerServiceMapping


class OrderExecutionTestCase(unittest.TestCase):
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
            partner_code="PTR-OEX-0001",
            partner_type="LABORATORY",
            legal_name="Order Execution Lab",
            display_name="Order Execution Lab",
            city="Ha Noi",
            status=PARTNER_ACTIVE,
        )
        db.session.add(self.partner)
        db.session.flush()

        self.mapping = PartnerServiceMapping(
            partner_id=self.partner.id,
            diagnostic_service_id=self.service.id,
            partner_service_code="OEX-HBA1C",
            partner_service_name="HbA1c",
            price=180000,
            status=MAPPING_ACTIVE,
        )
        db.session.add(self.mapping)

        self.collector = Driver(
            driver_code="COL-OEX-001",
            full_name="Order Execution Collector",
            status="ACTIVE",
        )
        db.session.add(self.collector)
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

    def _booking_with_assignment(self):
        slot = SchedulingService.list_available_slots(self.partner.id)[0]
        booking = MarketplaceBookingService.create_booking(
            {
                "partner_service_mapping_id": self.mapping.id,
                "patient_name": "Execution Patient",
                "patient_phone": "0909333000",
                "requested_date": slot.slot_date,
            }
        )
        BookingAssignmentService.reserve_slot_for_booking(booking.id, slot.id)
        BookingAssignmentService.assign_collector(booking.id, self.collector.id)
        OrderLifecycleService.create_order_from_booking(booking.id)
        return booking

    def test_create_medical_order_from_booking(self):
        booking = self._booking_with_assignment()

        response = self.client.post(
            "/api/v1/order-execution/orders",
            json={"booking_id": booking.id},
        )
        self.assertEqual(response.status_code, 201)
        order = response.get_json()["order"]
        self.assertEqual(order["status"], MEDICAL_ORDER_BOOKED)
        self.assertTrue(order["barcode_value"].startswith("DXO-"))
        self.assertIn("DXCON:MEDICAL_ORDER:", order["qr_payload"])

        timeline = MedicalOrderEvent.query.filter_by(medical_order_id=order["id"]).count()
        self.assertGreaterEqual(timeline, 1)

    def test_state_machine_advance_and_complete(self):
        booking = self._booking_with_assignment()
        create = self.client.post(
            "/api/v1/order-execution/orders",
            json={"booking_id": booking.id},
        )
        order_id = create.get_json()["order"]["id"]

        advance = self.client.post(f"/api/v1/order-execution/orders/{order_id}/advance")
        self.assertEqual(advance.status_code, 200)
        advanced_status = advance.get_json()["order"]["status"]
        self.assertIn(
            advanced_status,
            [
                MEDICAL_ORDER_COLLECTOR_ASSIGNED,
                MEDICAL_ORDER_PAID,
                MEDICAL_ORDER_PAYMENT_PENDING,
                MEDICAL_ORDER_CONFIRMED,
            ],
        )

        order, executed = OrderWorkflowService.run_demo_execution_flow(order_id)
        self.assertEqual(order.status, MEDICAL_ORDER_COMPLETED)
        self.assertIn(MEDICAL_ORDER_SAMPLE_COLLECTED, executed)

    def test_barcode_label_incident_cancel_refund_recollect(self):
        booking = self._booking_with_assignment()
        order = OrderWorkflowService.create_from_booking(booking.id)
        OrderWorkflowService.transition(order.id, MEDICAL_ORDER_CONFIRMED)
        OrderWorkflowService.transition(order.id, MEDICAL_ORDER_PAYMENT_PENDING)
        OrderWorkflowService.transition(order.id, MEDICAL_ORDER_PAID)
        OrderWorkflowService.transition(
            order.id,
            MEDICAL_ORDER_COLLECTOR_ASSIGNED,
            collector_id=self.collector.id,
        )
        OrderWorkflowService.transition(order.id, MEDICAL_ORDER_COLLECTOR_EN_ROUTE)
        OrderWorkflowService.transition(order.id, MEDICAL_ORDER_ARRIVED)
        OrderWorkflowService.transition(order.id, MEDICAL_ORDER_SAMPLE_COLLECTED)

        barcode = self.client.get(f"/api/v1/order-execution/orders/{order.id}/barcode")
        self.assertEqual(barcode.status_code, 200)
        self.assertIn("sample_barcode", barcode.get_json())

        label = self.client.post(f"/api/v1/order-execution/orders/{order.id}/label")
        self.assertEqual(label.status_code, 201)
        self.assertEqual(SampleLabel.query.filter_by(medical_order_id=order.id).count(), 1)

        incident = self.client.post(
            f"/api/v1/order-execution/orders/{order.id}/incident",
            json={
                "incident_type": "TEMPERATURE_BREACH",
                "description": "Cold box temperature exceeded threshold",
            },
        )
        self.assertEqual(incident.status_code, 201)
        self.assertEqual(SampleIncident.query.filter_by(medical_order_id=order.id).count(), 1)

        recollect = self.client.post(
            f"/api/v1/order-execution/orders/{order.id}/recollect",
            json={"reason": "Hemolysis detected"},
        )
        self.assertEqual(recollect.status_code, 200)
        self.assertEqual(
            recollect.get_json()["order"]["status"],
            MEDICAL_ORDER_RECOLLECT_REQUIRED,
        )

        paid_order = OrderWorkflowService.create_from_booking(
            MarketplaceBookingService.create_booking(
                {
                    "partner_service_mapping_id": self.mapping.id,
                    "patient_name": "Refund Patient",
                    "patient_phone": "0909444000",
                    "requested_date": SchedulingService.list_available_slots(self.partner.id)[0].slot_date,
                }
            ).id
        )
        OrderWorkflowService.transition(paid_order.id, MEDICAL_ORDER_CONFIRMED)
        OrderWorkflowService.transition(paid_order.id, MEDICAL_ORDER_PAYMENT_PENDING)
        OrderWorkflowService.transition(paid_order.id, MEDICAL_ORDER_PAID)

        refund = self.client.post(f"/api/v1/order-execution/orders/{paid_order.id}/refund")
        self.assertEqual(refund.status_code, 200)
        self.assertEqual(refund.get_json()["order"]["status"], MEDICAL_ORDER_REFUNDED)

        cancel_order = OrderWorkflowService.create_from_booking(
            MarketplaceBookingService.create_booking(
                {
                    "partner_service_mapping_id": self.mapping.id,
                    "patient_name": "Cancel Patient",
                    "patient_phone": "0909555000",
                    "requested_date": SchedulingService.list_available_slots(self.partner.id)[0].slot_date,
                }
            ).id
        )
        cancel = self.client.post(f"/api/v1/order-execution/orders/{cancel_order.id}/cancel")
        self.assertEqual(cancel.status_code, 200)
        self.assertEqual(cancel.get_json()["order"]["status"], MEDICAL_ORDER_CANCELLED)

    def test_routes_registered(self):
        routes = {str(rule) for rule in self.app.url_map.iter_rules()}
        self.assertIn("/api/v1/order-execution/orders", routes)
        self.assertIn("/order-execution", routes)


if __name__ == "__main__":
    unittest.main()
