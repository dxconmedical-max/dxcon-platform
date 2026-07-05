"""MDM validation — required fields, types, duplicate detection."""

from __future__ import annotations

from typing import Any

from app.mdm.registry import ENTITY_SCHEMAS, validate_entity_type
from app.models.mdm import MdmMasterRecord, ROW_DUPLICATE, ROW_ERROR, ROW_VALID


class MdmValidationError(ValueError):
    pass


def normalize_row(entity_type: str, raw: dict[str, Any]) -> dict[str, str]:
    validate_entity_type(entity_type)
    schema = ENTITY_SCHEMAS[entity_type]
    allowed = set(schema.get("required", [])) | set(schema.get("optional", [])) | {"code", "name", "status"}
    normalized: dict[str, str] = {}
    for key, value in raw.items():
        col = str(key).strip().lower().replace(" ", "_")
        if col in allowed or col in ("code", "name", "status", "parent_code", "tenant_id", "external_id"):
            normalized[col] = "" if value is None else str(value).strip()
    return normalized


def validate_row(
    entity_type: str,
    row: dict[str, str],
    *,
    existing_codes: set[str] | None = None,
    batch_codes: set[str] | None = None,
) -> tuple[str, list[str]]:
    validate_entity_type(entity_type)
    schema = ENTITY_SCHEMAS[entity_type]
    errors: list[str] = []

    code = (row.get("code") or "").strip()
    name = (row.get("name") or "").strip()
    if not code:
        errors.append("code is required")
    if not name:
        errors.append("name is required")

    for field in schema.get("required", []):
        if field in ("code", "name"):
            continue
        if not (row.get(field) or "").strip():
            errors.append(f"{field} is required")

    if code and batch_codes and code in batch_codes:
        errors.append(f"duplicate code in import file: {code}")

    if errors:
        if any("duplicate" in e for e in errors):
            return ROW_DUPLICATE, errors
        return ROW_ERROR, errors
    if code and existing_codes and code in existing_codes:
        return ROW_DUPLICATE, [f"duplicate code in master data: {code}"]
    return ROW_VALID, []


def load_existing_codes(entity_type: str) -> set[str]:
    rows = MdmMasterRecord.query.filter_by(entity_type=entity_type).with_entities(MdmMasterRecord.code).all()
    return {r[0] for r in rows}
