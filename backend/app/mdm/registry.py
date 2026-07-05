"""MDM entity registry — schemas for all 18 master data modules."""

from __future__ import annotations

from typing import Any

ENTITY_TYPES: tuple[str, ...] = (
    "test_catalog",
    "test_package",
    "sample_type",
    "tube_type",
    "instrument",
    "laboratory",
    "clinic",
    "doctor",
    "collector",
    "department",
    "insurance",
    "price_list",
    "contract",
    "payment_method",
    "reference_range",
    "icd10",
    "loinc",
    "notification_template",
)

ENTITY_LABELS: dict[str, str] = {
    "test_catalog": "Test Catalog",
    "test_package": "Test Packages",
    "sample_type": "Sample Types",
    "tube_type": "Tube Types",
    "instrument": "Instruments",
    "laboratory": "Laboratories",
    "clinic": "Clinics",
    "doctor": "Doctors",
    "collector": "Collectors",
    "department": "Departments",
    "insurance": "Insurance",
    "price_list": "Price Lists",
    "contract": "Contracts",
    "payment_method": "Payment Methods",
    "reference_range": "Reference Ranges",
    "icd10": "ICD-10 Registry",
    "loinc": "LOINC Registry",
    "notification_template": "Notification Templates",
}

# code + name are always required; additional attribute columns per entity
ENTITY_SCHEMAS: dict[str, dict[str, Any]] = {
    "test_catalog": {
        "required": ["code", "name"],
        "optional": ["category", "sample_type", "price", "loinc_code", "unit", "turnaround_hours"],
        "legacy_sync": "test_catalogs",
    },
    "test_package": {
        "required": ["code", "name"],
        "optional": ["description", "package_price", "test_codes", "status"],
        "legacy_sync": None,
    },
    "sample_type": {
        "required": ["code", "name"],
        "optional": ["description", "collection_instructions", "storage_temp"],
        "legacy_sync": None,
    },
    "tube_type": {
        "required": ["code", "name"],
        "optional": ["color", "additive", "volume_ml", "sample_type_code"],
        "legacy_sync": None,
    },
    "instrument": {
        "required": ["code", "name"],
        "optional": ["manufacturer", "model", "serial_number", "laboratory_code", "status"],
        "legacy_sync": "lab_analyzers",
    },
    "laboratory": {
        "required": ["code", "name"],
        "optional": ["address", "phone", "email", "accreditation", "tenant_id"],
        "legacy_sync": "laboratories",
    },
    "clinic": {
        "required": ["code", "name"],
        "optional": ["address", "phone", "email", "specialty", "tenant_id"],
        "legacy_sync": "clinic_profiles",
    },
    "doctor": {
        "required": ["code", "name"],
        "optional": ["specialty", "license_number", "phone", "email", "clinic_code"],
        "legacy_sync": "doctor_profiles",
    },
    "collector": {
        "required": ["code", "name"],
        "optional": ["phone", "email", "region", "vehicle_type", "status"],
        "legacy_sync": None,
    },
    "department": {
        "required": ["code", "name"],
        "optional": ["parent_code", "organization_code", "department_type"],
        "legacy_sync": None,
    },
    "insurance": {
        "required": ["code", "name"],
        "optional": ["payer_type", "contact_phone", "contact_email", "policy_prefix"],
        "legacy_sync": None,
    },
    "price_list": {
        "required": ["code", "name"],
        "optional": ["currency", "effective_from", "effective_to", "contract_code"],
        "legacy_sync": "crm_price_books",
    },
    "contract": {
        "required": ["code", "name"],
        "optional": ["party_code", "start_date", "end_date", "contract_type", "discount_percent"],
        "legacy_sync": "contracts",
    },
    "payment_method": {
        "required": ["code", "name"],
        "optional": ["method_type", "provider", "fee_percent", "is_online"],
        "legacy_sync": "payment_methods",
    },
    "reference_range": {
        "required": ["code", "name"],
        "optional": ["test_code", "gender", "age_min", "age_max", "low_value", "high_value", "unit"],
        "legacy_sync": "reference_ranges",
    },
    "icd10": {
        "required": ["code", "name"],
        "optional": ["category", "chapter", "is_billable"],
        "legacy_sync": "standard_codes",
        "standard_system": "ICD10",
    },
    "loinc": {
        "required": ["code", "name"],
        "optional": ["component", "system", "property", "scale", "method"],
        "legacy_sync": "standard_codes",
        "standard_system": "LOINC",
    },
    "notification_template": {
        "required": ["code", "name"],
        "optional": ["channel", "subject", "body_template", "locale"],
        "legacy_sync": "notification_templates",
    },
}


def template_columns(entity_type: str) -> list[str]:
    schema = ENTITY_SCHEMAS.get(entity_type, {})
    cols = ["code", "name"]
    for col in schema.get("optional", []):
        if col not in cols:
            cols.append(col)
    return cols


def sample_row(entity_type: str) -> dict[str, str]:
    samples: dict[str, dict[str, str]] = {
        "test_catalog": {
            "code": "CBC",
            "name": "Complete Blood Count",
            "category": "Hematology",
            "sample_type": "BLOOD",
            "price": "150000",
            "loinc_code": "58410-2",
            "unit": "panel",
            "turnaround_hours": "24",
        },
        "test_package": {
            "code": "PKG-EXEC",
            "name": "Executive Health Panel",
            "description": "Annual executive screening",
            "package_price": "2500000",
            "test_codes": "CBC;GLU;LIPID",
            "status": "active",
        },
        "sample_type": {
            "code": "BLOOD",
            "name": "Whole Blood",
            "description": "Venous blood draw",
            "collection_instructions": "Fasting 8h",
            "storage_temp": "2-8C",
        },
        "tube_type": {
            "code": "EDTA-PURPLE",
            "name": "EDTA Tube",
            "color": "purple",
            "additive": "EDTA",
            "volume_ml": "4",
            "sample_type_code": "BLOOD",
        },
        "instrument": {
            "code": "AUTO-001",
            "name": "Hematology Analyzer",
            "manufacturer": "Sysmex",
            "model": "XN-1000",
            "serial_number": "SN12345",
            "laboratory_code": "LAB-HCM",
            "status": "active",
        },
        "laboratory": {
            "code": "LAB-HCM",
            "name": "DxCon HCMC Central Lab",
            "address": "District 1, HCMC",
            "phone": "0281234567",
            "email": "lab@dxcon.test",
            "accreditation": "ISO15189",
            "tenant_id": "",
        },
        "clinic": {
            "code": "CLINIC-001",
            "name": "DxCon Partner Clinic",
            "address": "District 7, HCMC",
            "phone": "0287654321",
            "email": "clinic@dxcon.test",
            "specialty": "General",
            "tenant_id": "",
        },
        "doctor": {
            "code": "DR-001",
            "name": "Dr. Nguyen Van A",
            "specialty": "Internal Medicine",
            "license_number": "BN12345",
            "phone": "0901234567",
            "email": "doctor@dxcon.test",
            "clinic_code": "CLINIC-001",
        },
        "collector": {
            "code": "COL-001",
            "name": "Collector Team Alpha",
            "phone": "0909876543",
            "email": "collector@dxcon.test",
            "region": "HCMC",
            "vehicle_type": "motorbike",
            "status": "active",
        },
        "department": {
            "code": "DEPT-LAB",
            "name": "Central Laboratory",
            "parent_code": "",
            "organization_code": "LAB-HCM",
            "department_type": "laboratory",
        },
        "insurance": {
            "code": "INS-BV",
            "name": "Bao Viet Insurance",
            "payer_type": "private",
            "contact_phone": "1900558899",
            "contact_email": "claims@baoviet.test",
            "policy_prefix": "BV",
        },
        "price_list": {
            "code": "PL-2026",
            "name": "Standard Price List 2026",
            "currency": "VND",
            "effective_from": "2026-01-01",
            "effective_to": "2026-12-31",
            "contract_code": "CTR-001",
        },
        "contract": {
            "code": "CTR-001",
            "name": "Corporate Wellness Contract",
            "party_code": "CLINIC-001",
            "start_date": "2026-01-01",
            "end_date": "2026-12-31",
            "contract_type": "corporate",
            "discount_percent": "10",
        },
        "payment_method": {
            "code": "CASH",
            "name": "Cash",
            "method_type": "cash",
            "provider": "counter",
            "fee_percent": "0",
            "is_online": "false",
        },
        "reference_range": {
            "code": "RR-GLU-F",
            "name": "Glucose Fasting Female",
            "test_code": "GLU",
            "gender": "female",
            "age_min": "18",
            "age_max": "65",
            "low_value": "70",
            "high_value": "99",
            "unit": "mg/dL",
        },
        "icd10": {
            "code": "E11.9",
            "name": "Type 2 diabetes mellitus without complications",
            "category": "Endocrine",
            "chapter": "IV",
            "is_billable": "true",
        },
        "loinc": {
            "code": "2345-7",
            "name": "Glucose [Mass/volume] in Serum or Plasma",
            "component": "Glucose",
            "system": "Serum/Plasma",
            "property": "MCnc",
            "scale": "Qn",
            "method": "",
        },
        "notification_template": {
            "code": "RESULT-READY",
            "name": "Result Ready SMS",
            "channel": "sms",
            "subject": "",
            "body_template": "Your result for {{test_name}} is ready.",
            "locale": "vi",
        },
    }
    row = {col: "" for col in template_columns(entity_type)}
    row.update(samples.get(entity_type, {"code": "SAMPLE-001", "name": "Sample Record"}))
    return row


def validate_entity_type(entity_type: str) -> None:
    if entity_type not in ENTITY_TYPES:
        raise ValueError(f"Unknown entity type: {entity_type}")
