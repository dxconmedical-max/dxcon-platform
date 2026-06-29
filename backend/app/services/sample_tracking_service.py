from datetime import datetime

from app.core.statuses import (
    MEDICAL_SAMPLE_COLLECTED,
    MEDICAL_SAMPLE_CREATED,
    MEDICAL_SAMPLE_IN_TRANSIT,
    MEDICAL_SAMPLE_PROCESSING,
    MEDICAL_SAMPLE_RECEIVED,
    MEDICAL_SAMPLE_RECOLLECT,
    MEDICAL_SAMPLE_REJECTED,
    SAMPLE_LABEL_PENDING,
    SAMPLE_LABEL_PRINTED,
)
from app.extensions.db import db
from app.models.medical_order import MedicalOrder
from app.models.medical_sample import Sample
from app.models.sample_label import SampleLabel
from app.models.sample_tracking import SampleTracking
from app.services.barcode_service import (
    generate_sample_codes,
    generate_unique_sample_code,
)
from app.services.label_print_service import LabelPrintService


class SampleTrackingServiceError(Exception):

    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class SampleTrackingService:

    @staticmethod
    def _get_order_or_raise(medical_order_id):
        order = MedicalOrder.query.get(medical_order_id)
        if not order:
            raise SampleTrackingServiceError("Medical order not found", 404)
        return order

    @staticmethod
    def create_sample(medical_order_id, sample_type=None):
        order = SampleTrackingService._get_order_or_raise(medical_order_id)

        existing = Sample.query.filter_by(medical_order_id=order.id).first()
        if existing:
            return existing

        sample_code = generate_unique_sample_code()
        codes = generate_sample_codes(sample_code)
        sample = Sample(
            sample_code=sample_code,
            medical_order_id=order.id,
            sample_type=sample_type,
            barcode_value=codes["barcode_value"],
            qr_payload=codes["qr_payload"],
            status=MEDICAL_SAMPLE_CREATED,
        )
        db.session.add(sample)
        db.session.flush()

        tracking = SampleTracking(
            sample_code=sample_code,
            marketplace_booking_id=order.marketplace_booking_id,
            medical_order_id=order.id,
            medical_sample_id=sample.id,
            collector_id=order.collector_id,
            status=MEDICAL_SAMPLE_CREATED,
        )
        db.session.add(tracking)
        db.session.commit()
        return sample, tracking

    @staticmethod
    def get_sample_for_order(medical_order_id):
        return Sample.query.filter_by(medical_order_id=medical_order_id).first()

    @staticmethod
    def get_tracking_for_order(medical_order_id):
        return SampleTracking.query.filter_by(medical_order_id=medical_order_id).first()

    @staticmethod
    def update_sample_status(medical_order_id, status, latitude=None, longitude=None):
        sample = SampleTrackingService.get_sample_for_order(medical_order_id)
        if not sample:
            raise SampleTrackingServiceError("Sample not found for order", 404)

        tracking = SampleTrackingService.get_tracking_for_order(medical_order_id)
        sample.status = status
        sample.updated_at = datetime.utcnow()

        if status == MEDICAL_SAMPLE_COLLECTED:
            sample.collected_at = datetime.utcnow()

        if tracking:
            tracking.status = status
            if latitude is not None:
                tracking.latitude = str(latitude)
            if longitude is not None:
                tracking.longitude = str(longitude)
            tracking.updated_at = datetime.utcnow()

        db.session.commit()
        return sample, tracking

    @staticmethod
    def create_label(medical_order_id, template_name="STANDARD", mark_printed=False):
        order = SampleTrackingService._get_order_or_raise(medical_order_id)
        sample = SampleTrackingService.get_sample_for_order(medical_order_id)
        if not sample:
            sample, _tracking = SampleTrackingService.create_sample(medical_order_id)

        payload = LabelPrintService.build_sample_label(order, sample)
        label = SampleLabel(
            medical_order_id=order.id,
            sample_id=sample.id,
            label_code=payload["label_code"],
            template_name=template_name,
            print_payload=LabelPrintService.serialize_label(payload),
            status=SAMPLE_LABEL_PRINTED if mark_printed else SAMPLE_LABEL_PENDING,
            printed_at=datetime.utcnow() if mark_printed else None,
        )
        db.session.add(label)
        db.session.commit()
        return label, payload

    @staticmethod
    def list_labels(medical_order_id):
        return SampleLabel.query.filter_by(medical_order_id=medical_order_id).order_by(
            SampleLabel.created_at.desc()
        ).all()
