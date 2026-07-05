"""MDM import engine — parse, validate, preview, approve, commit, rollback."""

from __future__ import annotations

import csv
import io
import uuid
from datetime import datetime, timezone
from typing import Any

from app.extensions.db import db
from app.mdm.audit import write_mdm_audit
from app.mdm.registry import ENTITY_SCHEMAS, template_columns, validate_entity_type
from app.mdm.sync import sync_record_to_legacy
from app.mdm.validation import load_existing_codes, normalize_row, validate_row
from app.models.mdm import (
    IMPORT_APPROVED,
    IMPORT_COMMITTED,
    IMPORT_FAILED,
    IMPORT_PENDING,
    IMPORT_ROLLED_BACK,
    IMPORT_VALIDATED,
    MDM_ACTIVE,
    MDM_INACTIVE,
    MdmImportBatch,
    MdmImportRow,
    MdmMasterRecord,
    ROW_COMMITTED,
    ROW_DUPLICATE,
    ROW_ERROR,
    ROW_SKIPPED,
    ROW_VALID,
)


class MdmImportError(ValueError):
    pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _batch_code() -> str:
    return f"MDM-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"


def parse_upload(entity_type: str, content: bytes, file_name: str) -> list[dict[str, str]]:
    validate_entity_type(entity_type)
    lower = (file_name or "").lower()
    if lower.endswith(".xlsx") or lower.endswith(".xls"):
        return _parse_excel(content)
    return _parse_csv(content)


def _parse_csv(content: bytes) -> list[dict[str, str]]:
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    rows: list[dict[str, str]] = []
    for raw in reader:
        if not any(str(v).strip() for v in raw.values() if v is not None):
            continue
        rows.append({str(k).strip().lower().replace(" ", "_"): ("" if v is None else str(v).strip()) for k, v in raw.items()})
    return rows


def _parse_excel(content: bytes) -> list[dict[str, str]]:
    try:
        import openpyxl
    except ImportError as exc:
        raise MdmImportError("Excel import requires openpyxl; use CSV or install openpyxl") from exc
    wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    ws = wb.active
    iterator = ws.iter_rows(values_only=True)
    headers = [str(h or "").strip().lower().replace(" ", "_") for h in next(iterator)]
    rows: list[dict[str, str]] = []
    for values in iterator:
        if not values or not any(v is not None and str(v).strip() for v in values):
            continue
        row = {}
        for idx, header in enumerate(headers):
            if not header:
                continue
            val = values[idx] if idx < len(values) else ""
            row[header] = "" if val is None else str(val).strip()
        rows.append(row)
    return rows


def create_import_batch(
    entity_type: str,
    *,
    file_name: str,
    file_format: str,
    rows: list[dict[str, str]],
    actor: str | None = None,
) -> MdmImportBatch:
    validate_entity_type(entity_type)
    existing = load_existing_codes(entity_type)
    batch = MdmImportBatch(
        batch_code=_batch_code(),
        entity_type=entity_type,
        file_name=file_name,
        file_format=file_format,
        total_rows=len(rows),
        status=IMPORT_PENDING,
        created_by=actor,
    )
    db.session.add(batch)
    db.session.flush()

    seen_in_batch: set[str] = set()
    valid_n = dup_n = err_n = 0
    preview_rows: list[dict] = []

    for idx, raw in enumerate(rows, start=1):
        normalized = normalize_row(entity_type, raw)
        status, errors = validate_row(
            entity_type,
            normalized,
            existing_codes=existing,
            batch_codes=seen_in_batch,
        )
        code = normalized.get("code", "")
        if code:
            seen_in_batch.add(code)
            if status == ROW_VALID and code in existing:
                status = ROW_DUPLICATE
                errors = [f"duplicate code in master data: {code}"]
        if status == ROW_VALID:
            valid_n += 1
        elif status == ROW_DUPLICATE:
            dup_n += 1
        else:
            err_n += 1

        import_row = MdmImportRow(
            batch_id=batch.id,
            row_number=idx,
            code=code or None,
            name=normalized.get("name") or None,
            status=status,
            validation_errors="; ".join(errors) if errors else None,
        )
        import_row.set_payload(normalized)
        db.session.add(import_row)
        if idx <= 50:
            preview_rows.append({
                "row_number": idx,
                "code": code,
                "name": normalized.get("name"),
                "status": status,
                "errors": errors,
            })

    batch.valid_rows = valid_n
    batch.duplicate_rows = dup_n
    batch.error_rows = err_n
    batch.status = IMPORT_VALIDATED if err_n == 0 else IMPORT_PENDING
    batch.set_preview({"sample": preview_rows, "columns": template_columns(entity_type)})
    write_mdm_audit(
        action="import.validate",
        entity_type=entity_type,
        entity_id=batch.batch_code,
        actor=actor,
        note=f"rows={len(rows)} valid={valid_n} dup={dup_n} err={err_n}",
    )
    return batch


def approve_batch(batch_id: str, *, actor: str | None = None) -> MdmImportBatch:
    batch = MdmImportBatch.query.get(batch_id)
    if not batch:
        raise MdmImportError("Import batch not found")
    if batch.status not in {IMPORT_PENDING, IMPORT_VALIDATED}:
        raise MdmImportError(f"Cannot approve batch in status {batch.status}")
    if batch.error_rows > 0:
        raise MdmImportError("Batch has validation errors; fix file and re-import")
    batch.status = IMPORT_APPROVED
    batch.approved_by = actor
    batch.approved_at = _utcnow()
    write_mdm_audit(action="import.approve", entity_type=batch.entity_type, entity_id=batch.batch_code, actor=actor)
    return batch


def commit_batch(batch_id: str, *, actor: str | None = None, skip_duplicates: bool = True) -> MdmImportBatch:
    batch = MdmImportBatch.query.get(batch_id)
    if not batch:
        raise MdmImportError("Import batch not found")
    if batch.status != IMPORT_APPROVED:
        raise MdmImportError(f"Batch must be approved before commit; status={batch.status}")

    schema = ENTITY_SCHEMAS[batch.entity_type]
    required = set(schema.get("required", []))
    optional = set(schema.get("optional", []))
    attr_keys = (required | optional) - {"code", "name"}

    committed = 0
    try:
        for row in MdmImportRow.query.filter_by(batch_id=batch.id).order_by(MdmImportRow.row_number).all():
            if row.status == ROW_ERROR:
                row.status = ROW_SKIPPED
                continue
            if row.status == ROW_DUPLICATE and skip_duplicates:
                row.status = ROW_SKIPPED
                continue
            if row.status not in {ROW_VALID, ROW_DUPLICATE}:
                continue

            payload = row.payload()
            code = (payload.get("code") or "").strip()
            name = (payload.get("name") or "").strip()
            existing = MdmMasterRecord.query.filter_by(entity_type=batch.entity_type, code=code).first()
            if existing:
                if skip_duplicates:
                    row.status = ROW_SKIPPED
                    continue
                raise MdmImportError(f"Duplicate master record: {code}")

            attrs = {k: payload[k] for k in attr_keys if k in payload and payload[k]}
            record = MdmMasterRecord(
                entity_type=batch.entity_type,
                code=code,
                name=name,
                status=payload.get("status") or MDM_ACTIVE,
                parent_code=payload.get("parent_code") or None,
                tenant_id=payload.get("tenant_id") or None,
                external_id=payload.get("external_id") or None,
                import_batch_id=batch.id,
                created_by=actor,
                updated_by=actor,
                source="import",
            )
            record.set_attributes(attrs)
            db.session.add(record)
            db.session.flush()
            sync_record_to_legacy(record)
            row.status = ROW_COMMITTED
            row.master_record_id = record.id
            committed += 1

        batch.committed_rows = committed
        batch.status = IMPORT_COMMITTED
        batch.committed_by = actor
        batch.committed_at = _utcnow()
        write_mdm_audit(
            action="import.commit",
            entity_type=batch.entity_type,
            entity_id=batch.batch_code,
            actor=actor,
            note=f"committed={committed}",
        )
    except Exception as exc:
        db.session.rollback()
        batch = MdmImportBatch.query.get(batch_id)
        if batch:
            batch.status = IMPORT_FAILED
            batch.error_summary = str(exc)
        raise MdmImportError(str(exc)) from exc
    return batch


def rollback_batch(batch_id: str, *, actor: str | None = None) -> MdmImportBatch:
    batch = MdmImportBatch.query.get(batch_id)
    if not batch:
        raise MdmImportError("Import batch not found")
    if batch.status != IMPORT_COMMITTED:
        raise MdmImportError(f"Only committed batches can be rolled back; status={batch.status}")

    from app.mdm.sync import deactivate_legacy

    for row in MdmImportRow.query.filter_by(batch_id=batch.id, status=ROW_COMMITTED).all():
        if not row.master_record_id:
            continue
        record = MdmMasterRecord.query.get(row.master_record_id)
        if record:
            record.status = MDM_INACTIVE
            record.updated_by = actor
            deactivate_legacy(record)
        row.status = ROW_SKIPPED

    batch.status = IMPORT_ROLLED_BACK
    batch.rolled_back_by = actor
    batch.rolled_back_at = _utcnow()
    write_mdm_audit(action="import.rollback", entity_type=batch.entity_type, entity_id=batch.batch_code, actor=actor)
    return batch


def import_from_bytes(
    entity_type: str,
    content: bytes,
    *,
    file_name: str,
    actor: str | None = None,
    auto_approve: bool = False,
    auto_commit: bool = False,
) -> MdmImportBatch:
    rows = parse_upload(entity_type, content, file_name)
    if not rows:
        raise MdmImportError("No data rows found in upload")
    fmt = "xlsx" if (file_name or "").lower().endswith((".xlsx", ".xls")) else "csv"
    batch = create_import_batch(entity_type, file_name=file_name, file_format=fmt, rows=rows, actor=actor)
    if auto_approve and batch.error_rows == 0:
        approve_batch(batch.id, actor=actor)
    if auto_commit and batch.status == IMPORT_APPROVED:
        commit_batch(batch.id, actor=actor)
    return batch
