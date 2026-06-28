import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import create_app
from app.core.statuses import (
    DEFAULT_PARTNER_VERIFICATION_ITEMS,
    MAPPING_ACTIVE,
    MARKETPLACE_VISIBLE_PARTNER_STATUSES,
    PARTNER_ACTIVE,
    VERIFICATION_VERIFIED,
)
from app.extensions.db import db
from app.models.diagnostic_category import DiagnosticCategory
from app.models.diagnostic_service import DiagnosticService
from app.models.partner import Partner
from app.models.partner_service_mapping import PartnerServiceMapping
from app.models.partner_verification_item import PartnerVerificationItem
from app.models.service_package import ServicePackage
from app.models.service_package_item import ServicePackageItem
from app.services.partner_availability import PartnerAvailabilityService


PARTNER_TYPE_PREFIX = {
    "LABORATORY": "LAB",
    "CLINIC": "CLN",
    "HOSPITAL": "HSP",
    "DOCTOR": "DOC",
    "CORPORATE": "CRP",
    "HOME_CARE": "HMC",
    "IMAGING_CENTER": "IMG",
}


def _generate_partner_code(partner_type):
    prefix = PARTNER_TYPE_PREFIX.get(partner_type, "PTR")
    count = Partner.query.filter(Partner.partner_code.like(f"{prefix}-%")).count()
    return f"{prefix}-{count + 1:04d}"


def _create_demo_partner(data):
    partner = Partner(
        partner_code=_generate_partner_code(data["partner_type"]),
        partner_type=data["partner_type"],
        legal_name=data["legal_name"],
        display_name=data["display_name"],
        province=data.get("province"),
        city=data.get("city"),
        district=data.get("district"),
        phone=data.get("phone"),
        email=data.get("email"),
        rating=data.get("rating", 0.0),
        review_count=data.get("review_count", 0),
        completed_orders=data.get("completed_orders", 0),
        average_result_time_hours=data.get("average_result_time_hours"),
        pickup_sla_minutes=data.get("pickup_sla_minutes"),
        response_sla_minutes=data.get("response_sla_minutes"),
        working_hours_summary=data.get("working_hours_summary"),
        api_status=data.get("api_status", "MANUAL_UPLOAD"),
        status=data.get("status", PARTNER_ACTIVE),
    )
    db.session.add(partner)
    db.session.flush()

    for item_type in DEFAULT_PARTNER_VERIFICATION_ITEMS:
        db.session.add(
            PartnerVerificationItem(
                partner_id=partner.id,
                item_type=item_type,
                status=VERIFICATION_VERIFIED,
                verified_by="demo-seed",
            )
        )

    db.session.commit()
    return partner


CATEGORIES = [
    ("HEMATOLOGY", "Hematology", "Blood cell and coagulation tests"),
    ("BIOCHEMISTRY", "Biochemistry", "Blood chemistry and metabolic panels"),
    ("ENDOCRINOLOGY", "Endocrinology", "Hormone and diabetes-related tests"),
    ("IMMUNOLOGY", "Immunology", "Inflammation and immune markers"),
    ("MICROBIOLOGY", "Microbiology", "Infection screening tests"),
    ("CARDIOLOGY", "Cardiology Markers", "Cardiac risk and enzyme tests"),
    ("LIVER", "Liver Function", "Hepatic enzyme and function tests"),
    ("KIDNEY", "Kidney Function", "Renal function and electrolytes"),
    ("VITAMIN", "Vitamin & Nutrition", "Vitamin and micronutrient tests"),
    ("GENERAL", "General Screening", "Preventive health screening tests"),
]

FEATURED_SERVICES = [
    ("CBC", "Complete Blood Count", "CBC", "HEMATOLOGY", "Whole Blood", False, 6, True),
    ("GLU", "Glucose", "Glucose", "BIOCHEMISTRY", "Serum", True, 4, True),
    ("HBA1C", "HbA1c", "HbA1c", "ENDOCRINOLOGY", "Whole Blood", False, 24, True),
    ("ALT", "ALT (SGPT)", "ALT", "LIVER", "Serum", False, 6, True),
    ("AST", "AST (SGOT)", "AST", "LIVER", "Serum", False, 6, True),
    ("CREAT", "Creatinine", "Creatinine", "KIDNEY", "Serum", False, 6, True),
    ("LIPID", "Lipid Panel", "Lipid Panel", "BIOCHEMISTRY", "Serum", True, 8, True),
    ("VITD", "Vitamin D", "Vitamin D", "VITAMIN", "Serum", False, 48, True),
    ("TSH", "TSH", "TSH", "ENDOCRINOLOGY", "Serum", False, 24, True),
    ("CRP", "CRP", "CRP", "IMMUNOLOGY", "Serum", False, 12, True),
]

SERVICE_SUFFIXES = [
    "Screening",
    "Follow-up",
    "Premium",
    "Express",
    "Basic",
    "Advanced",
    "Panel A",
    "Panel B",
    "Combo",
    "Profile",
]

PACKAGES = [
    ("PKG-DIABETES", "Diabetes Care Panel", "Diabetes monitoring bundle", "Diabetes", 450000, ["HBA1C", "GLU"]),
    ("PKG-LIVER", "Liver Health Panel", "Liver enzyme screening", "Liver disease", 380000, ["ALT", "AST"]),
    ("PKG-KIDNEY", "Kidney Function Panel", "Renal health screening", "Kidney disease", 320000, ["CREAT"]),
    ("PKG-LIPID", "Heart Risk Panel", "Cardiovascular risk screening", "Dyslipidemia", 420000, ["LIPID"]),
    ("PKG-CBC-BASIC", "Basic Blood Panel", "General blood screening", "Anemia screening", 180000, ["CBC"]),
    ("PKG-THYROID", "Thyroid Panel", "Thyroid hormone screening", "Thyroid disorder", 350000, ["TSH"]),
    ("PKG-INFLAMMATION", "Inflammation Panel", "Inflammation marker screening", "Inflammation", 290000, ["CRP"]),
    ("PKG-VITAMIN", "Vitamin D Check", "Vitamin D deficiency screening", "Vitamin deficiency", 520000, ["VITD"]),
    ("PKG-METABOLIC", "Metabolic Starter", "Starter metabolic screening", "Metabolic syndrome", 560000, ["GLU", "LIPID", "CREAT"]),
    ("PKG-WELLNESS", "Annual Wellness", "Annual preventive screening", "Preventive care", 890000, ["CBC", "GLU", "LIPID", "TSH"]),
]

DEMO_PARTNERS = [
    {
        "partner_type": "LABORATORY",
        "legal_name": "DxCon Demo Lab Hanoi JSC",
        "display_name": "DxCon Demo Lab Hanoi",
        "province": "Ha Noi",
        "city": "Ha Noi",
        "district": "Cau Giay",
        "phone": "02439990001",
        "email": "hanoi.lab@dxcon.test",
        "rating": 4.8,
        "review_count": 256,
        "completed_orders": 1420,
        "average_result_time_hours": 12,
        "pickup_sla_minutes": 90,
        "response_sla_minutes": 20,
        "working_hours_summary": "Mon-Sat 06:30-20:00",
    },
    {
        "partner_type": "CLINIC",
        "legal_name": "Saigon Diagnostic Clinic",
        "display_name": "Saigon Diagnostic Clinic",
        "province": "Ho Chi Minh",
        "city": "Ho Chi Minh",
        "district": "District 3",
        "phone": "02839990002",
        "email": "saigon.clinic@dxcon.test",
        "rating": 4.5,
        "review_count": 180,
        "completed_orders": 980,
        "average_result_time_hours": 18,
        "pickup_sla_minutes": 120,
        "response_sla_minutes": 30,
        "working_hours_summary": "Mon-Sun 07:00-21:00",
    },
    {
        "partner_type": "HOSPITAL",
        "legal_name": "MediCare Hospital Laboratory",
        "display_name": "MediCare Hospital Lab",
        "province": "Da Nang",
        "city": "Da Nang",
        "district": "Hai Chau",
        "phone": "023639990003",
        "email": "danang.lab@dxcon.test",
        "rating": 4.7,
        "review_count": 210,
        "completed_orders": 1150,
        "average_result_time_hours": 10,
        "pickup_sla_minutes": 60,
        "response_sla_minutes": 15,
        "working_hours_summary": "24/7 laboratory service",
    },
]


def _get_or_create_categories():
    created = 0
    category_map = {}

    for code, name, description in CATEGORIES:
        category = DiagnosticCategory.query.filter_by(category_code=code).first()
        if not category:
            category = DiagnosticCategory(
                category_code=code,
                name=name,
                description=description,
                is_active=True,
            )
            db.session.add(category)
            created += 1
        category_map[code] = category

    db.session.flush()
    return category_map, created


def _get_or_create_services(category_map):
    created = 0
    service_map = {}

    base_definitions = []
    for code, name, short_name, category_code, sample_type, fasting, eta, home in FEATURED_SERVICES:
        base_definitions.append(
            {
                "service_code": code,
                "name": name,
                "short_name": short_name,
                "category_code": category_code,
                "sample_type": sample_type,
                "fasting_required": fasting,
                "estimated_turnaround_hours": eta,
                "home_collection_allowed": home,
            }
        )

    category_codes = [item[0] for item in CATEGORIES]
    idx = 0
    while len(base_definitions) < 100:
        template = FEATURED_SERVICES[idx % len(FEATURED_SERVICES)]
        suffix = SERVICE_SUFFIXES[(len(base_definitions) // len(FEATURED_SERVICES)) % len(SERVICE_SUFFIXES)]
        code = f"{template[0]}-{len(base_definitions)+1:03d}"
        base_definitions.append(
            {
                "service_code": code,
                "name": f"{template[1]} {suffix}",
                "short_name": f"{template[2]} {suffix}",
                "category_code": category_codes[idx % len(category_codes)],
                "sample_type": template[4],
                "fasting_required": template[5],
                "estimated_turnaround_hours": template[6] + (len(base_definitions) % 5),
                "home_collection_allowed": template[7],
            }
        )
        idx += 1

    for item in base_definitions:
        service = DiagnosticService.query.filter_by(service_code=item["service_code"]).first()
        if not service:
            service = DiagnosticService(
                service_code=item["service_code"],
                name=item["name"],
                short_name=item["short_name"],
                category_id=category_map[item["category_code"]].id,
                sample_type=item["sample_type"],
                preparation_instruction="Follow standard pre-test instructions.",
                fasting_required=item["fasting_required"],
                estimated_turnaround_hours=item["estimated_turnaround_hours"],
                home_collection_allowed=item["home_collection_allowed"],
                is_active=True,
            )
            db.session.add(service)
            created += 1
        service_map[item["service_code"]] = service

    db.session.flush()
    return service_map, created


def _get_or_create_packages(service_map):
    created = 0

    for code, name, description, target, price, service_codes in PACKAGES:
        package = ServicePackage.query.filter_by(package_code=code).first()
        if not package:
            package = ServicePackage(
                package_code=code,
                name=name,
                description=description,
                target_condition=target,
                base_price=price,
                is_active=True,
            )
            db.session.add(package)
            db.session.flush()
            created += 1

            for service_code in service_codes:
                service = service_map.get(service_code)
                if service:
                    db.session.add(
                        ServicePackageItem(
                            package_id=package.id,
                            diagnostic_service_id=service.id,
                            quantity=1,
                        )
                    )

    return created


def _ensure_demo_partners():
    created = 0
    partners = Partner.query.filter(
        Partner.status.in_(MARKETPLACE_VISIBLE_PARTNER_STATUSES)
    ).limit(3).all()

    if len(partners) >= 3:
        return partners, created

    for item in DEMO_PARTNERS:
        existing = Partner.query.filter_by(display_name=item["display_name"]).first()
        if existing:
            partners.append(existing)
            continue

        partner = _create_demo_partner(
            {
                **item,
                "api_status": "MANUAL_UPLOAD",
                "status": PARTNER_ACTIVE,
            }
        )

        partners.append(partner)
        created += 1

    return partners, created


def _create_mappings(partners, service_map):
    created = 0
    featured_codes = [item[0] for item in FEATURED_SERVICES]

    for partner_index, partner in enumerate(partners):
        price_factor = 1.0 + (partner_index * 0.08)
        for service_index, service_code in enumerate(featured_codes):
            service = service_map[service_code]
            mapping_code = f"{partner.partner_code}-{service_code}"

            existing = PartnerServiceMapping.query.filter_by(
                partner_id=partner.id,
                diagnostic_service_id=service.id,
            ).first()
            if existing:
                continue

            base_price = 120000 + (service_index * 15000)
            db.session.add(
                PartnerServiceMapping(
                    partner_id=partner.id,
                    diagnostic_service_id=service.id,
                    partner_service_code=mapping_code,
                    partner_service_name=service.name,
                    price=round(base_price * price_factor, -3),
                    currency="VND",
                    turnaround_hours=service.estimated_turnaround_hours,
                    home_collection_available=service.home_collection_allowed,
                    status=MAPPING_ACTIVE,
                )
            )
            created += 1

        extra_codes = list(service_map.keys())[10:25]
        for offset, service_code in enumerate(extra_codes):
            service = service_map[service_code]
            existing = PartnerServiceMapping.query.filter_by(
                partner_id=partner.id,
                diagnostic_service_id=service.id,
            ).first()
            if existing:
                continue

            db.session.add(
                PartnerServiceMapping(
                    partner_id=partner.id,
                    diagnostic_service_id=service.id,
                    partner_service_code=f"{partner.partner_code}-{service.service_code}",
                    partner_service_name=service.name,
                    price=round((90000 + offset * 8000) * price_factor, -3),
                    currency="VND",
                    turnaround_hours=service.estimated_turnaround_hours,
                    home_collection_available=service.home_collection_allowed,
                    status=MAPPING_ACTIVE,
                )
            )
            created += 1

    db.session.commit()
    return created


def _seed_partner_availability(partners):
    created = 0
    today = datetime.utcnow().strftime("%Y-%m-%d")

    for index, partner in enumerate(partners):
        availability = PartnerAvailabilityService.get_or_create(
            partner.id,
            today,
            maximum_daily_capacity=40,
        )
        target_booked = index * 14
        if availability.booked_count != target_booked:
            availability.booked_count = target_booked
            PartnerAvailabilityService.refresh_availability(availability)
            created += 1

    db.session.commit()
    return created


def seed_marketplace_demo():
    category_map, categories_created = _get_or_create_categories()
    service_map, services_created = _get_or_create_services(category_map)
    packages_created = _get_or_create_packages(service_map)
    partners, partners_created = _ensure_demo_partners()
    mappings_created = _create_mappings(partners, service_map)
    availability_created = _seed_partner_availability(partners)

    return {
        "categories_created": categories_created,
        "services_created": services_created,
        "packages_created": packages_created,
        "partners_created": partners_created,
        "mappings_created": mappings_created,
        "availability_created": availability_created,
        "categories_total": DiagnosticCategory.query.count(),
        "services_total": DiagnosticService.query.count(),
        "packages_total": ServicePackage.query.count(),
        "partners_total": Partner.query.count(),
        "mappings_total": PartnerServiceMapping.query.count(),
    }


def main():
    app = create_app()

    with app.app_context():
        db.create_all()
        summary = seed_marketplace_demo()

        print("\n=== DXCON MARKETPLACE DEMO SEED ===\n")
        for key, value in summary.items():
            print(f"{key}: {value}")
        print("\nMARKETPLACE DEMO SEED COMPLETE\n")


if __name__ == "__main__":
    main()
