import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app.core.statuses import (
    LAB_RESULT_RELEASED,
    PATIENT_CONSENT_DATA_PROCESSING,
    PATIENT_CONSENT_GRANTED,
)
from app.extensions.db import db
from app.models.patient import Patient
from app.models.patient_consent import PatientConsent
from app.models.patient_device import PatientDevice
from app.models.patient_notification_setting import PatientNotificationSetting
from app.models.patient_preference import PatientPreference
from app.models.patient_profile import PatientProfile
from app.services.marketplace_booking import MarketplaceBookingService
from app.services.order_workflow_service import OrderWorkflowService
from app.services.patient_portal_service import PatientPortalService
from app.services.result_gateway_service import (
    ResultApprovalService,
    ResultReleaseService,
    ResultReviewService,
    ResultUploadService,
    ResultValidationService,
)
from app.services.scheduling import SchedulingService


def seed_patient_portal_demo(patient_id=None):
    patient = Patient.query.get(patient_id) if patient_id else Patient.query.first()
    if not patient:
        patient = Patient(
            patient_code="PAT-PORTAL-001",
            full_name="Portal Demo Patient",
            gender="F",
            date_of_birth="1990-01-01",
            phone="0908111999",
            email="portal.patient@dxcon.vn",
        )
        db.session.add(patient)
        db.session.commit()

    profile = PatientProfile.query.filter_by(patient_id=patient.id).first()
    if not profile:
        profile = PatientProfile(
            patient_id=patient.id,
            qr_code=f"PQR-{patient.patient_code}",
            qr_payload=f'{{"patient_id":"{patient.id}","patient_code":"{patient.patient_code}"}}',
            favorite_doctors_json='[{"doctor_id":"DOC-001","name":"Dr. An"}]',
            favorite_clinics_json='[{"partner_id":"CLINIC-001","name":"DxCon Clinic"}]',
            family_members_json='[{"name":"Family Member","relation":"SPOUSE"}]',
        )
        db.session.add(profile)

    if not PatientPreference.query.filter_by(patient_id=patient.id).first():
        db.session.add(
            PatientPreference(
                patient_id=patient.id,
                pref_key="report_language",
                pref_value="vi",
            )
        )

    if not PatientDevice.query.filter_by(patient_id=patient.id).first():
        db.session.add(
            PatientDevice(
                patient_id=patient.id,
                device_type="MOBILE",
                device_name="iPhone",
                push_token="patient-firebase-token",
            )
        )

    if not PatientNotificationSetting.query.filter_by(patient_id=patient.id).first():
        db.session.add(
            PatientNotificationSetting(
                patient_id=patient.id,
                channel="EMAIL",
                template_code="RESULT_READY",
                is_enabled=True,
            )
        )

    if not PatientConsent.query.filter_by(patient_id=patient.id).first():
        db.session.add(
            PatientConsent(
                patient_id=patient.id,
                consent_type=PATIENT_CONSENT_DATA_PROCESSING,
                status=PATIENT_CONSENT_GRANTED,
            )
        )

    db.session.commit()
    return {"patient_id": patient.id, "profile_created": True}


def seed_patient_portal_flow(mapping):
    from app.models.partner_service_mapping import PartnerServiceMapping

    if not mapping:
        mapping = PartnerServiceMapping.query.first()
    if not mapping:
        return {"orders_created": 0}

    patient = Patient.query.filter_by(phone="0908111999").first()
    if not patient:
        summary = seed_patient_portal_demo()
        patient = Patient.query.get(summary["patient_id"])

    slots = SchedulingService.list_available_slots(mapping.partner_id)
    if not slots:
        return {"orders_created": 0}

    booking = MarketplaceBookingService.create_booking(
        {
            "partner_service_mapping_id": mapping.id,
            "patient_name": "Portal Demo Patient",
            "patient_phone": "0908111999",
            "requested_date": slots[0].slot_date,
        }
    )
    order = OrderWorkflowService.create_from_booking(booking.id)
    order.patient_id = patient.id if patient else None
    db.session.commit()

    result = ResultUploadService.create_manual(
        {
            "medical_order_id": order.id,
            "items": [
                {
                    "test_code": "GLU",
                    "test_name": "Glucose",
                    "result_value": "5.2",
                    "reference_range": "3.9-6.1",
                }
            ],
        }
    )
    ResultValidationService.validate(result.id)
    ResultReviewService.submit_review(result.id, {"comments": "Reviewed"})
    ResultApprovalService.approve(result.id, {"comments": "Approved"})
    ResultReleaseService.release(result.id, {})
    PatientPortalService._ensure_profile(patient.id)
    return {"orders_created": 1, "patient_id": patient.id, "lab_result_id": result.id}


def main():
    from app import create_app

    app = create_app()
    with app.app_context():
        db.create_all()
        summary = seed_patient_portal_demo()
        print("\n=== DXCON PATIENT PORTAL DEMO SEED ===\n")
        for key, value in summary.items():
            print(f"{key}: {value}")


if __name__ == "__main__":
    main()
