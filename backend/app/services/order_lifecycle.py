from datetime import datetime

from app.core.audit import write_audit
from app.core.events import write_event
from app.core.statuses import (
    BOOKING_TIMELINE_CONFIRMED,
    MARKETPLACE_BOOKING_ASSIGNED,
    MARKETPLACE_BOOKING_CONFIRMED,
    ORDER_CONFIRMED,
)
from app.extensions.db import db
from app.models.marketplace_booking import MarketplaceBooking
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.patient import Patient
from app.models.sample_collection import SampleCollection
from app.models.test_catalog import TestCatalog
from app.services.booking_assignment import BookingAssignmentService
from app.services.marketplace_booking import MarketplaceBookingService


class OrderLifecycleError(Exception):

    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class OrderLifecycleService:

    @staticmethod
    def _get_booking_or_raise(booking_id):
        booking = MarketplaceBooking.query.get(booking_id)
        if not booking:
            raise OrderLifecycleError("Booking not found", 404)
        return booking

    @staticmethod
    def _get_order_or_raise(order_id):
        order = Order.query.get(order_id)
        if not order:
            raise OrderLifecycleError("Order not found", 404)
        return order

    @staticmethod
    def _find_or_create_patient(booking):
        patient = Patient.query.filter_by(phone=booking.patient_phone).first()
        if patient:
            return patient

        count = Patient.query.count()
        patient = Patient(
            patient_code=f"PAT-{count + 1:06d}",
            full_name=booking.patient_name,
            phone=booking.patient_phone,
            email=booking.patient_email,
            address=booking.patient_address,
        )
        db.session.add(patient)
        db.session.flush()
        return patient

    @staticmethod
    def _resolve_test_catalog(diagnostic_service, price):
        catalog = TestCatalog.query.filter_by(code=diagnostic_service.service_code).first()
        if catalog:
            return catalog

        catalog = TestCatalog(
            code=diagnostic_service.service_code,
            name=diagnostic_service.name,
            category=diagnostic_service.sample_type,
            sample_type=diagnostic_service.sample_type,
            price=price or 0,
        )
        db.session.add(catalog)
        db.session.flush()
        return catalog

    @staticmethod
    def get_order_for_booking(booking_id):
        booking = OrderLifecycleService._get_booking_or_raise(booking_id)
        if booking.order_id:
            return Order.query.get(booking.order_id)

        return Order.query.filter_by(marketplace_booking_id=booking.id).first()

    @staticmethod
    def create_order_from_booking(
        booking_id,
        actor_email="SYSTEM",
        ip_address="",
    ):
        booking = OrderLifecycleService._get_booking_or_raise(booking_id)

        existing = OrderLifecycleService.get_order_for_booking(booking_id)
        if existing:
            return existing

        if booking.status not in (
            MARKETPLACE_BOOKING_ASSIGNED,
            MARKETPLACE_BOOKING_CONFIRMED,
        ):
            raise OrderLifecycleError(
                "Booking must be ASSIGNED or CONFIRMED before creating an order",
                409,
            )

        assignment = BookingAssignmentService.get_assignment_for_booking(booking.id)
        if booking.status == MARKETPLACE_BOOKING_ASSIGNED and not assignment:
            raise OrderLifecycleError(
                "Collector assignment is required before creating an order",
                409,
            )

        mapping = booking.partner_service_mapping
        if not mapping:
            raise OrderLifecycleError("Partner service mapping not found", 404)

        service = booking.diagnostic_service
        if not service:
            raise OrderLifecycleError("Diagnostic service not found", 404)

        patient = OrderLifecycleService._find_or_create_patient(booking)
        catalog = OrderLifecycleService._resolve_test_catalog(
            service,
            mapping.price,
        )

        order = Order(
            order_code=f"ORD-{booking.booking_code}",
            patient_id=patient.id,
            laboratory_id=booking.partner_id,
            status=ORDER_CONFIRMED,
            total_amount=mapping.price or 0,
        )
        db.session.add(order)
        db.session.flush()

        order_item = OrderItem(
            order_id=order.id,
            test_catalog_id=catalog.id,
            price=mapping.price or 0,
        )
        db.session.add(order_item)

        booking.order_id = order.id
        order.marketplace_booking_id = booking.id
        booking.updated_at = datetime.utcnow()

        if booking.status == MARKETPLACE_BOOKING_CONFIRMED:
            MarketplaceBookingService.write_timeline_event(
                booking,
                BOOKING_TIMELINE_CONFIRMED,
                message=f"Order {order.order_code} confirmed for booking {booking.booking_code}",
                actor_email=actor_email,
                audit_action="ORDER_CREATED_FROM_BOOKING",
                ip_address=ip_address,
            )
        else:
            write_audit(
                action="ORDER_CREATED_FROM_BOOKING",
                object_type="Order",
                object_id=order.id,
                user_email=actor_email,
                ip_address=ip_address,
            )
            write_event(
                event_type="ORDER_CREATED_FROM_BOOKING",
                object_type="Order",
                object_id=order.id,
                message=f"Order {order.order_code} created from booking {booking.booking_code}",
            )

        db.session.commit()
        return order

    @staticmethod
    def list_orders(status=None, partner_id=None):
        query = Order.query

        if status:
            query = query.filter(Order.status == status)

        if partner_id:
            query = query.filter(Order.laboratory_id == partner_id)

        return query.order_by(Order.created_at.desc()).all()

    @staticmethod
    def get_order_detail(order_id):
        order = OrderLifecycleService._get_order_or_raise(order_id)
        items = OrderItem.query.filter_by(order_id=order.id).all()
        collection = SampleCollection.query.filter_by(order_id=order.id).first()
        booking = None
        if order.marketplace_booking_id:
            booking = MarketplaceBooking.query.get(order.marketplace_booking_id)

        payload = order.to_dict()
        payload["items"] = [item.to_dict() for item in items]
        payload["collection"] = collection.to_dict() if collection else None
        payload["booking"] = booking.to_dict() if booking else None
        return payload
