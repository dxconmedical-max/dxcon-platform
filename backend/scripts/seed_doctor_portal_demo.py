import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app.extensions.db import db
from app.models.doctor_availability import DoctorAvailability
from app.models.doctor_commission import DoctorCommission
from app.models.doctor_patient import DoctorPatient
from app.models.doctor_profile import DoctorProfile
from app.models.doctor_specialty import DoctorSpecialty
from app.models.patient import Patient
from app.services.doctor_portal_service import DoctorPortalService


def seed_doctor_portal_demo():
    if DoctorProfile.query.first():
        profile = DoctorProfile.query.first()
        return {"doctor_id": profile.doctor_id, "already_seeded": True}

    profile = DoctorPortalService.ensure_profile(
        data={
            "doctor_code": "DOC-PORTAL-001",
            "full_name": "Dr. Portal Demo",
            "license_number": "VN-123456",
            "email": "doctor@dxcon.vn",
            "phone": "0908222333",
            "specialty_primary": "Internal Medicine",
            "favorite_services": [{"service_code": "GLU", "name": "Glucose"}],
            "linked_clinics": [{"partner_id": None, "name": "DxCon Clinic"}],
        }
    )

    db.session.add(
        DoctorSpecialty(
            doctor_id=profile.doctor_id,
            specialty_code="IM",
            specialty_name="Internal Medicine",
            is_primary=True,
        )
    )
    db.session.add(
        DoctorAvailability(
            doctor_id=profile.doctor_id,
            day_of_week="MON",
            start_time="08:00",
            end_time="12:00",
            location="DxCon Clinic",
        )
    )
    db.session.commit()
    return {"doctor_id": profile.doctor_id, "doctor_code": profile.doctor_code}


def seed_doctor_portal_flow(partner=None, mapping=None, patient=None):
    from app.models.partner_service_mapping import PartnerServiceMapping
    from scripts.seed_patient_portal_demo import seed_patient_portal_flow

    demo = seed_doctor_portal_demo()
    doctor_id = demo["doctor_id"]

    if not patient:
        patient = Patient.query.filter_by(phone="0908111999").first()
    flow = seed_patient_portal_flow(mapping)
    if not patient:
        patient = Patient.query.get(flow["patient_id"])

    DoctorPortalService.assign_patient(doctor_id, patient.id)
    db.session.add(
        DoctorCommission(
            commission_code="DOC-COM-001",
            doctor_id=doctor_id,
            medical_order_id=None,
            amount=150000,
            status="PAID",
        )
    )
    db.session.commit()
    return {
        "doctor_id": doctor_id,
        "patient_id": patient.id,
        "lab_result_id": flow.get("lab_result_id"),
    }


def main():
    from app import create_app

    app = create_app()
    with app.app_context():
        db.create_all()
        summary = seed_doctor_portal_demo()
        print("\n=== DXCON DOCTOR PORTAL DEMO SEED ===\n")
        for key, value in summary.items():
            print(f"{key}: {value}")


if __name__ == "__main__":
    main()
