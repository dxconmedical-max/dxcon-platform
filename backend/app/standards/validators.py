import json

from app.extensions.db import db
from app.models.healthcare_standards import StandardCode, StandardCodeSystem, StandardValidationLog
from app.standards.registry import StandardsRegistry


def validate_code_reference(system_code, code):
    errors = []
    if not StandardsRegistry.is_supported_system(system_code):
        errors.append(f"Unsupported code system: {system_code}")
        return {"valid": False, "errors": errors}

    system = StandardCodeSystem.query.filter_by(system_code=system_code).first()
    if system is None:
        errors.append(f"Code system not seeded: {system_code}")
        return {"valid": False, "errors": errors}

    row = StandardCode.query.filter_by(system_id=system.id, code=code).first()
    if row is None:
        errors.append(f"Unknown code {code} in {system_code}")
        return {"valid": False, "errors": errors}

    return {"valid": True, "errors": [], "display": row.display, "code_id": row.id}


def log_validation(standard_type, resource_type, status, detail=None):
    row = StandardValidationLog(
        standard_type=standard_type,
        resource_type=resource_type,
        status=status,
        detail_json=json.dumps(detail or {}),
    )
    db.session.add(row)
    db.session.commit()
    return row.to_dict()
