"""MDM service — CRUD, dashboard statistics, master record queries."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func

from app.extensions.db import db
from app.mdm.audit import write_mdm_audit
from app.mdm.registry import ENTITY_LABELS, ENTITY_TYPES, ENTITY_SCHEMAS, validate_entity_type
from app.mdm.sync import sync_record_to_legacy
from app.mdm.validation import load_existing_codes, normalize_row, validate_row
from app.models.mdm import (
    IMPORT_COMMITTED,
    IMPORT_ROLLED_BACK,
    MDM_ACTIVE,
    MDM_INACTIVE,
    MdmImportBatch,
    MdmMasterRecord,
    ROW_VALID,
)


class MdmServiceError(ValueError):
    pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def list_records(entity_type: str | None = None, *, status: str | None = None, limit: int = 100) -> list[dict]:
    query = MdmMasterRecord.query
    if entity_type:
        validate_entity_type(entity_type)
        query = query.filter_by(entity_type=entity_type)
    if status:
        query = query.filter_by(status=status)
    rows = query.order_by(MdmMasterRecord.entity_type, MdmMasterRecord.code).limit(limit).all()
    return [r.to_dict() for r in rows]


def get_record(entity_type: str, code: str) -> dict | None:
    row = MdmMasterRecord.query.filter_by(entity_type=entity_type, code=code).first()
    return row.to_dict() if row else None


def upsert_record(
    entity_type: str,
    data: dict[str, Any],
    *,
    actor: str | None = None,
    sync_legacy: bool = True,
) -> dict:
    validate_entity_type(entity_type)
    normalized = normalize_row(entity_type, data)
    code = normalized.get("code", "").strip()
    existing = load_existing_codes(entity_type)
    existing_row = MdmMasterRecord.query.filter_by(entity_type=entity_type, code=code).first()
    if existing_row:
        existing = existing - {code}
    status, errors = validate_row(entity_type, normalized, existing_codes=existing)
    if status != "valid" and errors:
        raise MdmServiceError("; ".join(errors))

    code = normalized["code"]
    name = normalized["name"]
    schema = ENTITY_SCHEMAS[entity_type]
    attr_keys = set(schema.get("optional", []))

    row = MdmMasterRecord.query.filter_by(entity_type=entity_type, code=code).first()
    is_new = row is None
    if is_new:
        row = MdmMasterRecord(entity_type=entity_type, code=code, name=name, created_by=actor)
        db.session.add(row)
    else:
        row.name = name
        row.updated_by = actor
        row.updated_at = _utcnow()

    row.status = normalized.get("status") or MDM_ACTIVE
    row.parent_code = normalized.get("parent_code") or row.parent_code
    row.tenant_id = normalized.get("tenant_id") or row.tenant_id
    attrs = {k: normalized[k] for k in attr_keys if k in normalized and normalized[k]}
    row.set_attributes(attrs)
    db.session.flush()
    if sync_legacy:
        sync_record_to_legacy(row)
    write_mdm_audit(
        action="record.create" if is_new else "record.update",
        entity_type=entity_type,
        entity_id=code,
        actor=actor,
    )
    return row.to_dict()


def deactivate_record(entity_type: str, code: str, *, actor: str | None = None) -> dict:
    row = MdmMasterRecord.query.filter_by(entity_type=entity_type, code=code).first()
    if not row:
        raise MdmServiceError("Record not found")
    row.status = MDM_INACTIVE
    row.updated_by = actor
    row.updated_at = _utcnow()
    write_mdm_audit(action="record.deactivate", entity_type=entity_type, entity_id=code, actor=actor)
    return row.to_dict()


def dashboard_stats() -> dict[str, Any]:
    total_by_entity = (
        db.session.query(MdmMasterRecord.entity_type, func.count(MdmMasterRecord.id))
        .group_by(MdmMasterRecord.entity_type)
        .all()
    )
    counts = {entity: 0 for entity in ENTITY_TYPES}
    for entity_type, count in total_by_entity:
        counts[entity_type] = count

    inactive = MdmMasterRecord.query.filter_by(status=MDM_INACTIVE).count()
    active = MdmMasterRecord.query.filter_by(status=MDM_ACTIVE).count()
    total = active + inactive

    duplicates: list[dict] = []
    dup_query = (
        db.session.query(MdmMasterRecord.entity_type, MdmMasterRecord.code, func.count(MdmMasterRecord.id))
        .group_by(MdmMasterRecord.entity_type, MdmMasterRecord.code)
        .having(func.count(MdmMasterRecord.id) > 1)
        .limit(20)
        .all()
    )
    for entity_type, code, count in dup_query:
        duplicates.append({"entity_type": entity_type, "code": code, "count": count})

    missing_entities = [e for e in ENTITY_TYPES if counts.get(e, 0) == 0]

    import_history = (
        MdmImportBatch.query.order_by(MdmImportBatch.created_at.desc()).limit(20).all()
    )

    return {
        "generated_at": _utcnow().isoformat(),
        "totals": {
            "records": total,
            "active": active,
            "inactive": inactive,
            "entity_types": len(ENTITY_TYPES),
            "populated_entity_types": sum(1 for c in counts.values() if c > 0),
        },
        "counts_by_entity": [
            {"entity_type": e, "label": ENTITY_LABELS.get(e, e), "count": counts.get(e, 0)}
            for e in ENTITY_TYPES
        ],
        "missing_data": missing_entities,
        "duplicate_records": duplicates,
        "inactive_records": inactive,
        "import_history": [b.to_dict() for b in import_history],
        "recent_commits": MdmImportBatch.query.filter_by(status=IMPORT_COMMITTED).count(),
        "rolled_back_batches": MdmImportBatch.query.filter_by(status=IMPORT_ROLLED_BACK).count(),
    }


def master_data_report() -> dict[str, Any]:
    stats = dashboard_stats()
    return {
        "report": "MASTER_DATA_REPORT",
        "generated_at": stats["generated_at"],
        "summary": stats["totals"],
        "entities": stats["counts_by_entity"],
        "missing_data": stats["missing_data"],
        "duplicates": stats["duplicate_records"],
    }
