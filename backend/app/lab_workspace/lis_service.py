"""LIS import engine — CSV/JSON with validation and failed rows."""

from __future__ import annotations

import csv
import io
import json
import uuid
from datetime import datetime
from typing import Any

from app.business_engine import service as biz
from app.business_engine.statuses import ORDER_LAB_RECEIVED, ORDER_PENDING_REVIEW, ORDER_RELEASED, ORDER_TESTING
from app.extensions.db import db
from app.lab_workspace.audit import write_lab_audit
from app.lab_workspace.flags import calculate_abnormal_flag
from app.models.biz_order import BizCollection, BizOrder, BizResult, BizResultItem
from app.models.lab_lis import (
    DEFAULT_FIELD_MAPPINGS,
    LISConnector,
    LISFieldMapping,
    LISImportBatch,
    LISImportFailedRow,
)
from app.models.patient import Patient
from app.models.test_catalog import TestCatalog


class LISImportError(ValueError):
    pass


def _utcnow() -> datetime:
    return datetime.utcnow()


def _batch_code() -> str:
    return f"LIS-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"


def seed_default_mappings(connector_id: str) -> None:
    for ext, dx in DEFAULT_FIELD_MAPPINGS.items():
        existing = LISFieldMapping.query.filter_by(connector_id=connector_id, external_field=ext).first()
        if existing:
            continue
        db.session.add(
            LISFieldMapping(connector_id=connector_id, external_field=ext, dxcon_field=dx, is_active=True)
        )
    db.session.flush()


def upsert_connector(data: dict[str, Any], *, actor: str | None = None) -> dict:
    code = (data.get("connector_code") or "").strip()
    name = (data.get("connector_name") or "").strip()
    if not code or not name:
        raise LISImportError("connector_code and connector_name are required")
    row = LISConnector.query.filter_by(connector_code=code).first()
    is_new = row is None
    if is_new:
        row = LISConnector(connector_code=code, connector_name=name)
        db.session.add(row)
    else:
        row.connector_name = name
        row.updated_at = _utcnow()
    for field in (
        "connector_type", "organization_id", "laboratory_id", "base_url", "auth_type",
        "username", "api_key_reference", "sftp_host", "sftp_path", "status",
    ):
        if field in data and data[field] is not None:
            setattr(row, field, data[field])
    db.session.flush()
    seed_default_mappings(row.id)
    write_lab_audit(action="connector_created" if is_new else "connector_updated", object_type="lis_connector", object_id=code, actor=actor)
    return row.to_dict()


def list_connectors(*, page: int = 1, per_page: int = 50) -> dict:
    query = LISConnector.query.order_by(LISConnector.connector_code)
    total = query.count()
    rows = query.offset((page - 1) * per_page).limit(per_page).all()
    return {"data": [r.to_dict() for r in rows], "pagination": {"page": page, "per_page": per_page, "total": total}}


def get_mappings(connector_id: str) -> list[dict]:
    return [m.to_dict() for m in LISFieldMapping.query.filter_by(connector_id=connector_id, is_active=True).all()]


def upsert_mapping(data: dict[str, Any], *, actor: str | None = None) -> dict:
    connector_id = data.get("connector_id")
    ext = data.get("external_field")
    dx = data.get("dxcon_field")
    if not connector_id or not ext or not dx:
        raise LISImportError("connector_id, external_field, dxcon_field required")
    row = LISFieldMapping.query.filter_by(connector_id=connector_id, external_field=ext).first()
    if not row:
        row = LISFieldMapping(connector_id=connector_id, external_field=ext, dxcon_field=dx)
        db.session.add(row)
    else:
        row.dxcon_field = dx
        row.transform_rule = data.get("transform_rule")
        row.is_active = data.get("is_active", True)
    db.session.flush()
    write_lab_audit(action="lis_mapping_updated", object_type="lis_mapping", object_id=f"{connector_id}:{ext}", actor=actor)
    return row.to_dict()


def _map_row(raw: dict, connector_id: str) -> dict:
    mappings = {m.external_field: m.dxcon_field for m in LISFieldMapping.query.filter_by(connector_id=connector_id, is_active=True).all()}
    if not mappings:
        mappings = DEFAULT_FIELD_MAPPINGS.copy()
    mapped: dict[str, Any] = {}
    for key, value in raw.items():
        target = mappings.get(key, key)
        mapped[target] = value
    return mapped


def _validate_import_row(mapped: dict, *, row_number: int) -> tuple[bool, str]:
    patient_code = mapped.get("patient_code") or mapped.get("external_patient_id")
    order_code = mapped.get("order_code") or mapped.get("external_order_id")
    sample_code = mapped.get("sample_code") or mapped.get("external_sample_id")
    test_code = mapped.get("test_code") or mapped.get("external_test_code")
    value = mapped.get("result_value") or mapped.get("value")

    if not patient_code or not Patient.query.get(str(patient_code)):
        return False, "patient not found"
    if not order_code:
        return False, "order_code missing"
    order = BizOrder.query.filter_by(order_code=str(order_code)).first()
    if not order:
        return False, "order not found"
    if order.status == ORDER_RELEASED:
        return False, "order already released"
    if sample_code:
        coll = BizCollection.query.filter_by(sample_code=str(sample_code)).first()
        if not coll:
            return False, "sample not found"
        if getattr(coll, "condition_status", None) == "rejected":
            return False, "sample rejected"
    if not test_code:
        return False, "test_code missing"
    catalog = TestCatalog.query.filter_by(code=str(test_code)).first()
    if not catalog:
        return False, "test not in master data"
    if not value:
        return False, "result_value missing"

    existing = (
        BizResultItem.query.join(BizResult, BizResultItem.result_id == BizResult.id)
        .filter(BizResult.order_id == order.id, BizResultItem.test_code == str(test_code))
        .first()
    )
    if existing and mapped.get("revision_mode") is not True:
        return False, "duplicate result"
    return True, ""


def _save_imported_result(mapped: dict, *, batch_id: str, actor: str | None) -> None:
    from app.business_engine.statuses import ORDER_LAB_RECEIVED, ORDER_TESTING

    order_code = str(mapped.get("order_code") or mapped.get("external_order_id"))
    test_code = str(mapped.get("test_code") or mapped.get("external_test_code"))
    catalog = TestCatalog.query.filter_by(code=test_code).first()
    ref = mapped.get("reference_range") or ""
    flag, _ = calculate_abnormal_flag(
        str(mapped.get("result_value") or ""),
        reference_range=ref,
        manual_flag=mapped.get("abnormal_flag") or mapped.get("flag"),
    )
    order = BizOrder.query.filter_by(order_code=order_code).first()
    if order.status not in {ORDER_LAB_RECEIVED, ORDER_TESTING, ORDER_PENDING_REVIEW}:
        if order.status == "in_transit":
            biz.receive_sample_at_lab(order_code, received_by=actor or "LIS", actor=actor)
        order = BizOrder.query.filter_by(order_code=order_code).first()
    result = BizResult.query.filter_by(order_id=order.id).first()
    if not result:
        result = BizResult(result_code=f"RPT-LIS-{order.order_code[-8:]}", order_id=order.id, status="testing")
        db.session.add(result)
        db.session.flush()
    item = BizResultItem(
        result_id=result.id,
        test_code=test_code,
        test_name=catalog.name if catalog else test_code,
        result_value=str(mapped.get("result_value")),
        unit=mapped.get("unit"),
        reference_range=ref,
        flag=flag.upper(),
        instrument=mapped.get("instrument"),
        technician=mapped.get("technician") or actor,
    )
    db.session.add(item)
    result.workflow_status = "validation_required"
    result.result_source = "imported"
    result.import_batch_id = batch_id
    result.status = "testing"
    if order.status == ORDER_LAB_RECEIVED:
        order.status = ORDER_TESTING
    write_lab_audit(action="result_imported", object_type="result", object_id=result.result_code, actor=actor)


def import_csv(
    content: bytes,
    *,
    connector_id: str,
    file_name: str = "import.csv",
    actor: str | None = None,
) -> dict:
    connector = LISConnector.query.get(connector_id)
    if not connector:
        raise LISImportError("connector not found")
    batch = LISImportBatch(
        batch_code=_batch_code(),
        connector_id=connector_id,
        import_type="CSV_UPLOAD",
        file_name=file_name,
        imported_by=actor,
    )
    db.session.add(batch)
    db.session.flush()

    reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig")))
    success = failed = 0
    for idx, raw in enumerate(reader, start=1):
        batch.total_rows += 1
        mapped = _map_row(raw, connector_id)
        ok, reason = _validate_import_row(mapped, row_number=idx)
        if not ok:
            failed += 1
            db.session.add(
                LISImportFailedRow(
                    batch_id=batch.id,
                    connector_id=connector_id,
                    row_number=idx,
                    error_reason=reason,
                    raw_payload=json.dumps(raw),
                )
            )
            write_lab_audit(action="result_import_failed", object_type="lis_import", object_id=batch.batch_code, actor=actor)
            continue
        try:
            _save_imported_result(mapped, batch_id=batch.id, actor=actor)
            success += 1
        except Exception as exc:
            failed += 1
            db.session.add(
                LISImportFailedRow(
                    batch_id=batch.id,
                    connector_id=connector_id,
                    row_number=idx,
                    error_reason=str(exc),
                    raw_payload=json.dumps(raw),
                )
            )
    batch.success_rows = success
    batch.failed_rows = failed
    batch.status = "completed" if failed == 0 else ("partial" if success else "failed")
    connector.last_sync_at = _utcnow()
    return batch.to_dict()


def import_json(
    payload: Any,
    *,
    connector_id: str,
    file_name: str = "import.json",
    actor: str | None = None,
) -> dict:
    connector = LISConnector.query.get(connector_id)
    if not connector:
        raise LISImportError("connector not found")
    rows = payload if isinstance(payload, list) else payload.get("results") or payload.get("data") or [payload]
    batch = LISImportBatch(
        batch_code=_batch_code(),
        connector_id=connector_id,
        import_type="JSON_UPLOAD",
        file_name=file_name,
        imported_by=actor,
    )
    db.session.add(batch)
    db.session.flush()
    success = failed = 0
    for idx, raw in enumerate(rows, start=1):
        if not isinstance(raw, dict):
            failed += 1
            continue
        batch.total_rows += 1
        mapped = _map_row(raw, connector_id)
        ok, reason = _validate_import_row(mapped, row_number=idx)
        if not ok:
            failed += 1
            db.session.add(
                LISImportFailedRow(
                    batch_id=batch.id,
                    connector_id=connector_id,
                    row_number=idx,
                    error_reason=reason,
                    raw_payload=json.dumps(raw),
                )
            )
            continue
        try:
            _save_imported_result(mapped, batch_id=batch.id, actor=actor)
            success += 1
        except Exception as exc:
            failed += 1
            db.session.add(
                LISImportFailedRow(
                    batch_id=batch.id,
                    connector_id=connector_id,
                    row_number=idx,
                    error_reason=str(exc),
                    raw_payload=json.dumps(raw),
                )
            )
    batch.success_rows = success
    batch.failed_rows = failed
    batch.status = "completed" if failed == 0 else ("partial" if success else "failed")
    connector.last_sync_at = _utcnow()
    return batch.to_dict()


def list_import_batches(*, limit: int = 50) -> list[dict]:
    return [b.to_dict() for b in LISImportBatch.query.order_by(LISImportBatch.created_at.desc()).limit(limit).all()]


def list_failed_imports(*, batch_id: str | None = None, limit: int = 100) -> list[dict]:
    query = LISImportFailedRow.query.filter_by(status="failed")
    if batch_id:
        query = query.filter_by(batch_id=batch_id)
    return [r.to_dict() for r in query.order_by(LISImportFailedRow.created_at.desc()).limit(limit).all()]


def retry_failed_import(failed_id: str, *, actor: str | None = None) -> dict:
    row = LISImportFailedRow.query.get(failed_id)
    if not row:
        raise LISImportError("failed row not found")
    raw = json.loads(row.raw_payload or "{}")
    mapped = _map_row(raw, row.connector_id or "")
    ok, reason = _validate_import_row(mapped, row_number=row.row_number or 0)
    if not ok:
        raise LISImportError(reason)
    _save_imported_result(mapped, batch_id=row.batch_id, actor=actor)
    row.status = "retried"
    row.retried_at = _utcnow()
    write_lab_audit(action="result_imported", object_type="lis_import_retry", object_id=failed_id, actor=actor)
    return row.to_dict()


def lis_integration_report() -> dict:
    return {
        "report": "LIS_INTEGRATION_REPORT",
        "connectors": LISConnector.query.count(),
        "import_batches": LISImportBatch.query.count(),
        "failed_rows": LISImportFailedRow.query.filter_by(status="failed").count(),
        "import_requires_validation": True,
        "auto_release_disabled": True,
        "adapters": ["REST_API", "HL7", "SFTP_FILE", "CSV_UPLOAD", "JSON_UPLOAD"],
    }


def lis_adapter_stub(adapter_type: str) -> dict:
    """Placeholder adapters for REST/HL7/SFTP — designed for future wiring."""
    return {
        "adapter": adapter_type,
        "status": "stub",
        "message": f"{adapter_type} adapter registered; implement polling/listener in production integration sprint",
    }
