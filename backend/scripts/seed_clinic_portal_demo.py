import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app.core.statuses import CLINIC_ORDER_COMPLETED, PARTNER_ACTIVE
from app.extensions.db import db
from app.models.clinic_department import ClinicDepartment
from app.models.clinic_profile import ClinicProfile
from app.models.partner import Partner
from app.services.clinic_portal_service import (
    ClinicBookingService,
    ClinicOrderService,
    ClinicPortalService,
)


def seed_clinic_portal_demo(partner=None):
    if ClinicProfile.query.first():
        profile = ClinicProfile.query.first()
        return {"clinic_id": profile.clinic_id, "already_seeded": True}

    if not partner:
        partner = Partner.query.filter_by(partner_type="CLINIC").first()
    if not partner:
        partner = Partner(
            partner_code="CLN-PORTAL-001",
            partner_type="CLINIC",
            legal_name="DxCon Clinic Portal",
            display_name="DxCon Clinic",
            status=PARTNER_ACTIVE,
        )
        db.session.add(partner)
        db.session.flush()

    profile = ClinicPortalService.ensure_profile(
        data={
            "clinic_code": "CLN-PORTAL-001",
            "name": "DxCon Clinic Portal",
            "legal_name": "DxCon Clinic Co., Ltd",
            "tax_code": "0109998888",
            "email": "clinic@dxcon.vn",
            "phone": "0908333444",
            "address": "123 Clinic Street, Hanoi",
            "partner_id": partner.id,
        }
    )

    db.session.add(
        ClinicDepartment(
            clinic_id=profile.clinic_id,
            department_code="LAB",
            name="Laboratory",
        )
    )
    db.session.commit()
    return {"clinic_id": profile.clinic_id, "clinic_code": profile.clinic_code, "partner_id": partner.id}


def seed_clinic_portal_flow(partner=None, mapping=None):
    from scripts.seed_doctor_portal_demo import seed_doctor_portal_demo

    demo = seed_clinic_portal_demo(partner=partner)
    clinic_id = demo["clinic_id"]

    doctor_demo = seed_doctor_portal_demo()
    doctor_id = doctor_demo["doctor_id"]

    from scripts.seed_patient_portal_demo import seed_patient_portal_flow

    flow = seed_patient_portal_flow(mapping)
    patient_id = flow["patient_id"]

    ClinicPortalService.link_doctor(clinic_id, doctor_id, role="CONSULTANT")
    ClinicPortalService.register_patient(clinic_id, patient_id)

    ClinicBookingService.create_booking(
        clinic_id,
        {
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "service_name": "General Checkup",
            "scheduled_at": (datetime.utcnow() + timedelta(days=2)).isoformat(),
        },
    )
    ClinicOrderService.create_order(
        clinic_id,
        {
            "patient_id": patient_id,
            "medical_order_id": flow.get("medical_order_id"),
            "total_amount": 350000,
            "status": CLINIC_ORDER_COMPLETED,
        },
    )

    return {
        "clinic_id": clinic_id,
        "doctor_id": doctor_id,
        "patient_id": patient_id,
    }


def main():
    from app import create_app

    app = create_app()
    with app.app_context():
        db.create_all()
        summary = seed_clinic_portal_demo()
        print("\n=== DXCON CLINIC PORTAL DEMO SEED ===\n")
        for key, value in summary.items():
            print(f"{key}: {value}")


if __name__ == "__main__":
    main()
