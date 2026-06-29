import json
from datetime import datetime

from app.core.audit import write_audit
from app.core.events import write_event
from app.core.statuses import (
    ASSIGNMENT_ACCEPTED,
    ASSIGNMENT_ASSIGNED,
    MEDICAL_ORDER_ARRIVED,
    MEDICAL_ORDER_BOOKED,
    MEDICAL_ORDER_CANCELLED,
    MEDICAL_ORDER_COLLECTOR_ASSIGNED,
    MEDICAL_ORDER_COLLECTOR_EN_ROUTE,
    MEDICAL_ORDER_COMPLETED,
    MEDICAL_ORDER_CONFIRMED,
    MEDICAL_ORDER_DELIVERED,
    MEDICAL_ORDER_IN_TRANSIT,
    MEDICAL_ORDER_PAID,
    MEDICAL_ORDER_PAYMENT_PENDING,
    MEDICAL_ORDER_PROCESSING,
    MEDICAL_ORDER_RECEIVED_BY_LAB,
    MEDICAL_ORDER_REFUNDED,
    MEDICAL_ORDER_REJECTED,
    MEDICAL_ORDER_REPORT_READY,
    MEDICAL_ORDER_RECOLLECT_REQUIRED,
    MEDICAL_ORDER_SAMPLE_COLLECTED,
    MEDICAL_ORDER_TRANSITIONS,
    MEDICAL_ORDER_VALIDATED,
    MEDICAL_SAMPLE_COLLECTED,
    MEDICAL_SAMPLE_IN_TRANSIT,
    MEDICAL_SAMPLE_PROCESSING,
    MEDICAL_SAMPLE_RECEIVED,
    RECOLLECT_PENDING,
    TERMINAL_MEDICAL_ORDER_STATUSES,
    VALID_MEDICAL_ORDER_STATUSES,
)
from app.extensions.db import db
from app.models.booking_assignment import BookingAssignment
from app.models.marketplace_booking import MarketplaceBooking
from app.models.medical_order import MedicalOrder
from app.models.medical_order_event import MedicalOrderEvent
from app.models.order import Order
from app.models.recollect_request import RecollectRequest
from app.services.barcode_service import generate_order_codes
from app.services.order_lifecycle import OrderLifecycleService
from app.services.sample_tracking_service import SampleTrackingService


class OrderWorkflowError(Exception):

    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class OrderWorkflowService:

    @staticmethod
    def _get_order_or_raise(order_id):
        order = MedicalOrder.query.get(order_id)
        if not order:
            raise OrderWorkflowError("Medical order not found", 404)
        return order

    @staticmethod
    def _generate_order_code():
        count = MedicalOrder.query.count()
        return f"MDO-{count + 1:06d}"

    @staticmethod
    def _write_event(
        order,
        event_type,
        message=None,
        from_status=None,
        to_status=None,
        actor_email="SYSTEM",
        metadata=None,
    ):
        event = MedicalOrderEvent(
            medical_order_id=order.id,
            event_type=event_type,
            from_status=from_status or order.status,
            to_status=to_status or order.status,
            message=message,
            actor_email=actor_email,
            metadata_json=json.dumps(metadata) if metadata else None,
        )
        db.session.add(event)
        return event

    @staticmethod
    def _can_transition(order, target_status):
        if order.status in TERMINAL_MEDICAL_ORDER_STATUSES:
            return False
        allowed = MEDICAL_ORDER_TRANSITIONS.get(order.status, [])
        return target_status in allowed

    @staticmethod
    def transition(
        order_id,
        target_status,
        message=None,
        actor_email="SYSTEM",
        ip_address="",
        collector_id=None,
        metadata=None,
    ):
        if target_status not in VALID_MEDICAL_ORDER_STATUSES:
            raise OrderWorkflowError(
                f"Invalid status. Must be one of: {', '.join(VALID_MEDICAL_ORDER_STATUSES)}"
            )

        order = OrderWorkflowService._get_order_or_raise(order_id)
        if not OrderWorkflowService._can_transition(order, target_status):
            raise OrderWorkflowError(
                f"Cannot transition from {order.status} to {target_status}",
                409,
            )

        previous_status = order.status
        order.status = target_status
        order.updated_at = datetime.utcnow()

        if collector_id:
            order.collector_id = collector_id

        if target_status == MEDICAL_ORDER_PAYMENT_PENDING:
            order.payment_status = "PENDING"
        elif target_status == MEDICAL_ORDER_PAID:
            order.payment_status = "PAID"
        elif target_status == MEDICAL_ORDER_REFUNDED:
            order.payment_status = "REFUNDED"

        OrderWorkflowService._write_event(
            order,
            event_type=f"STATUS_{target_status}",
            message=message or f"Order {order.order_code} transitioned to {target_status}",
            from_status=previous_status,
            to_status=target_status,
            actor_email=actor_email,
            metadata=metadata,
        )

        if target_status == MEDICAL_ORDER_SAMPLE_COLLECTED:
            SampleTrackingService.update_sample_status(order.id, MEDICAL_SAMPLE_COLLECTED)
        elif target_status == MEDICAL_ORDER_IN_TRANSIT:
            SampleTrackingService.update_sample_status(order.id, MEDICAL_SAMPLE_IN_TRANSIT)
        elif target_status == MEDICAL_ORDER_RECEIVED_BY_LAB:
            SampleTrackingService.update_sample_status(order.id, MEDICAL_SAMPLE_RECEIVED)
        elif target_status == MEDICAL_ORDER_PROCESSING:
            SampleTrackingService.update_sample_status(order.id, MEDICAL_SAMPLE_PROCESSING)

        write_audit(
            action=f"MEDICAL_ORDER_{target_status}",
            object_type="MedicalOrder",
            object_id=order.id,
            user_email=actor_email,
            ip_address=ip_address,
        )
        write_event(
            event_type=f"MEDICAL_ORDER_{target_status}",
            object_type="MedicalOrder",
            object_id=order.id,
            message=message or f"Medical order {order.order_code} reached {target_status}",
        )

        db.session.commit()
        return order

    @staticmethod
    def create_from_booking(
        booking_id,
        actor_email="SYSTEM",
        ip_address="",
    ):
        booking = MarketplaceBooking.query.get(booking_id)
        if not booking:
            raise OrderWorkflowError("Booking not found", 404)

        existing = MedicalOrder.query.filter_by(marketplace_booking_id=booking_id).first()
        if existing:
            return existing

        legacy_order = OrderLifecycleService.get_order_for_booking(booking_id)
        order_code = OrderWorkflowService._generate_order_code()
        codes = generate_order_codes(order_code)

        mapping = booking.partner_service_mapping
        total_amount = mapping.price if mapping else 0

        order = MedicalOrder(
            order_code=order_code,
            marketplace_booking_id=booking.id,
            legacy_order_id=legacy_order.id if legacy_order else None,
            patient_id=legacy_order.patient_id if legacy_order else None,
            patient_name=booking.patient_name,
            patient_phone=booking.patient_phone,
            partner_id=booking.partner_id,
            diagnostic_service_id=booking.diagnostic_service_id,
            status=MEDICAL_ORDER_BOOKED,
            total_amount=total_amount or 0,
            payment_status="UNPAID",
            barcode_value=codes["barcode_value"],
            qr_payload=codes["qr_payload"],
        )
        db.session.add(order)
        db.session.flush()

        OrderWorkflowService._write_event(
            order,
            event_type="ORDER_CREATED",
            message=f"Medical order {order.order_code} created from booking {booking.booking_code}",
            from_status=None,
            to_status=MEDICAL_ORDER_BOOKED,
            actor_email=actor_email,
        )

        SampleTrackingService.create_sample(
            order.id,
            sample_type=getattr(booking.diagnostic_service, "sample_type", None)
            if booking.diagnostic_service
            else None,
        )

        write_audit(
            action="MEDICAL_ORDER_CREATED",
            object_type="MedicalOrder",
            object_id=order.id,
            user_email=actor_email,
            ip_address=ip_address,
        )
        write_event(
            event_type="MEDICAL_ORDER_CREATED",
            object_type="MedicalOrder",
            object_id=order.id,
            message=f"Medical order {order.order_code} created",
        )

        db.session.commit()
        return order

    @staticmethod
    def list_orders(status=None, partner_id=None):
        query = MedicalOrder.query
        if status:
            query = query.filter(MedicalOrder.status == status)
        if partner_id:
            query = query.filter(MedicalOrder.partner_id == partner_id)
        return query.order_by(MedicalOrder.created_at.desc()).all()

    @staticmethod
    def get_order_detail(order_id):
        order = OrderWorkflowService._get_order_or_raise(order_id)
        timeline = OrderWorkflowService.list_timeline(order_id)
        sample = SampleTrackingService.get_sample_for_order(order_id)
        tracking = SampleTrackingService.get_tracking_for_order(order_id)
        labels = SampleTrackingService.list_labels(order_id)

        payload = order.to_dict()
        payload["timeline"] = [event.to_dict() for event in timeline]
        payload["sample"] = sample.to_dict() if sample else None
        payload["tracking"] = tracking.to_dict() if tracking else None
        payload["labels"] = [label.to_dict() for label in labels]
        return payload

    @staticmethod
    def list_timeline(order_id):
        OrderWorkflowService._get_order_or_raise(order_id)
        return MedicalOrderEvent.query.filter_by(
            medical_order_id=order_id
        ).order_by(MedicalOrderEvent.created_at.asc()).all()

    @staticmethod
    def get_barcode(order_id):
        order = OrderWorkflowService._get_order_or_raise(order_id)
        sample = SampleTrackingService.get_sample_for_order(order_id)
        payload = {
            "order_code": order.order_code,
            "barcode_value": order.barcode_value,
            "qr_payload": order.qr_payload,
        }
        if sample:
            payload["sample_code"] = sample.sample_code
            payload["sample_barcode"] = sample.barcode_value
            payload["sample_qr"] = sample.qr_payload
        return payload

    @staticmethod
    def cancel_order(order_id, reason=None, actor_email="SYSTEM", ip_address=""):
        return OrderWorkflowService.transition(
            order_id,
            MEDICAL_ORDER_CANCELLED,
            message=reason or "Order cancelled",
            actor_email=actor_email,
            ip_address=ip_address,
        )

    @staticmethod
    def refund_order(order_id, reason=None, actor_email="SYSTEM", ip_address=""):
        order = OrderWorkflowService._get_order_or_raise(order_id)
        if order.status not in (MEDICAL_ORDER_PAID, MEDICAL_ORDER_PAYMENT_PENDING):
            raise OrderWorkflowError("Order must be paid or payment pending to refund", 409)
        return OrderWorkflowService.transition(
            order_id,
            MEDICAL_ORDER_REFUNDED,
            message=reason or "Order refunded",
            actor_email=actor_email,
            ip_address=ip_address,
        )

    @staticmethod
    def request_recollect(
        order_id,
        reason,
        scheduled_date=None,
        actor_email="SYSTEM",
        ip_address="",
    ):
        if not reason:
            raise OrderWorkflowError("reason is required for recollect")

        order = OrderWorkflowService._get_order_or_raise(order_id)
        sample = SampleTrackingService.get_sample_for_order(order_id)

        recollect = RecollectRequest(
            medical_order_id=order.id,
            sample_id=sample.id if sample else None,
            reason=reason,
            status=RECOLLECT_PENDING,
            requested_by=actor_email,
            scheduled_date=scheduled_date,
        )
        db.session.add(recollect)

        order = OrderWorkflowService.transition(
            order_id,
            MEDICAL_ORDER_RECOLLECT_REQUIRED,
            message=reason,
            actor_email=actor_email,
            ip_address=ip_address,
            metadata={"recollect_request": True},
        )
        return order, recollect

    @staticmethod
    def advance_booking_workflow(order_id, actor_email="SYSTEM", ip_address=""):
        order = OrderWorkflowService._get_order_or_raise(order_id)
        booking = MarketplaceBooking.query.get(order.marketplace_booking_id)
        if not booking:
            raise OrderWorkflowError("Linked booking not found", 404)

        steps = []

        if order.status == MEDICAL_ORDER_BOOKED:
            order = OrderWorkflowService.transition(
                order_id, MEDICAL_ORDER_CONFIRMED, actor_email=actor_email, ip_address=ip_address
            )
            steps.append(MEDICAL_ORDER_CONFIRMED)

        if order.status == MEDICAL_ORDER_CONFIRMED:
            order = OrderWorkflowService.transition(
                order_id,
                MEDICAL_ORDER_PAYMENT_PENDING,
                actor_email=actor_email,
                ip_address=ip_address,
            )
            steps.append(MEDICAL_ORDER_PAYMENT_PENDING)

        if order.status == MEDICAL_ORDER_PAYMENT_PENDING:
            order = OrderWorkflowService.transition(
                order_id, MEDICAL_ORDER_PAID, actor_email=actor_email, ip_address=ip_address
            )
            steps.append(MEDICAL_ORDER_PAID)

        assignment = BookingAssignment.query.filter(
            BookingAssignment.booking_id == booking.id,
            BookingAssignment.assignment_status.in_(
                [ASSIGNMENT_ASSIGNED, ASSIGNMENT_ACCEPTED]
            ),
        ).first()
        if assignment and order.status == MEDICAL_ORDER_PAID:
            order = OrderWorkflowService.transition(
                order_id,
                MEDICAL_ORDER_COLLECTOR_ASSIGNED,
                collector_id=assignment.collector_id,
                actor_email=actor_email,
                ip_address=ip_address,
            )
            steps.append(MEDICAL_ORDER_COLLECTOR_ASSIGNED)

        return order, steps

    @staticmethod
    def run_demo_execution_flow(order_id, actor_email="SYSTEM", ip_address=""):
        order, _steps = OrderWorkflowService.advance_booking_workflow(
            order_id,
            actor_email=actor_email,
            ip_address=ip_address,
        )

        flow = [
            MEDICAL_ORDER_COLLECTOR_EN_ROUTE,
            MEDICAL_ORDER_ARRIVED,
            MEDICAL_ORDER_SAMPLE_COLLECTED,
            MEDICAL_ORDER_IN_TRANSIT,
            MEDICAL_ORDER_RECEIVED_BY_LAB,
            MEDICAL_ORDER_PROCESSING,
            MEDICAL_ORDER_VALIDATED,
            MEDICAL_ORDER_REPORT_READY,
            MEDICAL_ORDER_DELIVERED,
            MEDICAL_ORDER_COMPLETED,
        ]

        executed = []
        for status in flow:
            if OrderWorkflowService._can_transition(order, status):
                order = OrderWorkflowService.transition(
                    order.id,
                    status,
                    actor_email=actor_email,
                    ip_address=ip_address,
                )
                executed.append(status)

        return order, executed
