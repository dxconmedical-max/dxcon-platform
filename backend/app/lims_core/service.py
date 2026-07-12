"""LIMS Core service — specimen lifecycle, barcodes, accessions, dashboard."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import func

from app.core.statuses import (
    LIMS_BARCODE_FORMAT_CODE128,
    LIMS_BARCODE_FORMAT_QR,
    LIMS_CONTAINER_TYPES,
    LIMS_SPECIMEN_ACCESSIONED,
    LIMS_SPECIMEN_ARCHIVED,
    LIMS_SPECIMEN_COLLECTED,
    LIMS_SPECIMEN_CREATED,
    LIMS_SPECIMEN_IN_TRANSIT,
    LIMS_SPECIMEN_LIFECYCLE,
    LIMS_SPECIMEN_PROCESSING,
    LIMS_SPECIMEN_QC,
    LIMS_SPECIMEN_RECEIVED,
    LIMS_SPECIMEN_REPORTED,
    LIMS_SPECIMEN_TRANSITIONS,
    LIMS_SPECIMEN_VALIDATING,
)
from app.extensions.db import db
from app.lims_core.audit import write_lims_audit
from app.models.lims_core import (
    LimsAccession,
    LimsBarcodeLog,
    LimsContainer,
    LimsSampleStatusHistory,
    LimsSpecimen,
    LimsStorageLocation,
)


class LimsCoreError(ValueError):
    pass


def _utcnow() -> datetime:
    return datetime.utcnow()


def _record_transition(
    specimen: LimsSpecimen,
    *,
    from_status: str | None,
    to_status: str,
    actor: str | None = None,
    note: str | None = None,
) -> None:
    db.session.add(
        LimsSampleStatusHistory(
            specimen_id=specimen.id,
            from_status=from_status,
            to_status=to_status,
            actor=actor,
            note=note,
            transitioned_at=_utcnow(),
        )
    )


def next_human_readable_barcode() -> str:
    """Pattern DXYYYYMMDD000001 — unique human-readable specimen id."""
    today = _utcnow().strftime("%Y%m%d")
    prefix = f"DX{today}"
    last = (
        LimsSpecimen.query.filter(LimsSpecimen.human_readable.like(f"{prefix}%"))
        .order_by(LimsSpecimen.human_readable.desc())
        .first()
    )
    if last:
        try:
            seq = int(last.human_readable[len(prefix) :]) + 1
        except ValueError:
            seq = 1
    else:
        seq = 1
    return f"{prefix}{seq:06d}"


def generate_barcode(
    *,
    specimen_id: str | None = None,
    formats: list[str] | None = None,
    generated_by: str | None = None,
    actor: str | None = None,
) -> dict[str, Any]:
    """Generate unique barcode(s) for a specimen. No duplicates."""
    human = next_human_readable_barcode()
    requested = formats or [LIMS_BARCODE_FORMAT_CODE128, LIMS_BARCODE_FORMAT_QR]
    outputs: list[dict] = []

    for fmt in requested:
        if fmt not in (LIMS_BARCODE_FORMAT_CODE128, LIMS_BARCODE_FORMAT_QR):
            raise LimsCoreError(f"Unsupported barcode format: {fmt}")
        value = human if fmt == LIMS_BARCODE_FORMAT_CODE128 else f"DXCON|SPECIMEN|{human}"
        if LimsBarcodeLog.query.filter_by(barcode_value=value).first():
            raise LimsCoreError("Barcode collision — retry")
        log = LimsBarcodeLog(
            barcode_value=value,
            human_readable=human,
            format=fmt,
            specimen_id=specimen_id,
            generated_by=generated_by,
        )
        db.session.add(log)
        outputs.append(log.to_dict())

    if specimen_id:
        specimen = LimsSpecimen.query.get(specimen_id)
        if specimen:
            specimen.barcode = outputs[0]["barcode_value"]
            specimen.human_readable = human

    write_lims_audit(action="barcode_generated", object_type="barcode", object_id=human, actor=actor)
    return {"human_readable": human, "barcodes": outputs}


def create_specimen(
    *,
    order_id: str | None = None,
    order_code: str | None = None,
    patient_code: str | None = None,
    organization_id: str | None = None,
    container_type: str | None = None,
    volume: float | None = None,
    volume_unit: str = "mL",
    collected_at: datetime | None = None,
    expires_at: datetime | None = None,
    actor: str | None = None,
) -> dict:
    if container_type and container_type not in LIMS_CONTAINER_TYPES:
        raise LimsCoreError(f"Invalid container_type: {container_type}")

    human = next_human_readable_barcode()
    code128_value = human
    qr_value = f"DXCON|SPECIMEN|{human}"

    specimen = LimsSpecimen(
        barcode=code128_value,
        human_readable=human,
        order_id=order_id,
        order_code=order_code,
        patient_code=patient_code,
        organization_id=organization_id,
        status=LIMS_SPECIMEN_CREATED,
        container_type=container_type,
        volume=volume,
        volume_unit=volume_unit,
        collected_at=collected_at,
        expires_at=expires_at or (collected_at + timedelta(hours=72) if collected_at else None),
    )
    db.session.add(specimen)
    db.session.flush()

    for fmt, value in (
        (LIMS_BARCODE_FORMAT_CODE128, code128_value),
        (LIMS_BARCODE_FORMAT_QR, qr_value),
    ):
        db.session.add(
            LimsBarcodeLog(
                barcode_value=value,
                human_readable=human,
                format=fmt,
                specimen_id=specimen.id,
                generated_by=actor,
            )
        )

    if container_type:
        db.session.add(
            LimsContainer(
                container_code=f"C-{human}",
                container_type=container_type,
                volume_capacity=volume,
                volume_unit=volume_unit,
                specimen_id=specimen.id,
            )
        )

    _record_transition(specimen, from_status=None, to_status=LIMS_SPECIMEN_CREATED, actor=actor, note="Specimen created")
    write_lims_audit(action="specimen_created", object_type="specimen", object_id=specimen.id, actor=actor)
    return specimen.to_dict()


def transition_specimen(
    specimen_id: str,
    *,
    to_status: str,
    actor: str | None = None,
    note: str | None = None,
) -> dict:
    if to_status not in LIMS_SPECIMEN_LIFECYCLE:
        raise LimsCoreError(f"Invalid status: {to_status}")
    specimen = LimsSpecimen.query.get(specimen_id)
    if not specimen:
        raise LimsCoreError("Specimen not found")
    allowed = LIMS_SPECIMEN_TRANSITIONS.get(specimen.status, set())
    if to_status not in allowed and to_status != specimen.status:
        raise LimsCoreError(f"Cannot transition {specimen.status} → {to_status}")

    from_status = specimen.status
    if from_status == to_status:
        return specimen.to_dict()

    specimen.status = to_status
    specimen.updated_at = _utcnow()
    _record_transition(specimen, from_status=from_status, to_status=to_status, actor=actor, note=note)
    write_lims_audit(
        action="specimen_status_changed",
        object_type="specimen",
        object_id=specimen.id,
        actor=actor,
    )
    return specimen.to_dict()


def get_specimen(specimen_id: str) -> dict:
    specimen = LimsSpecimen.query.get(specimen_id)
    if not specimen:
        raise LimsCoreError("Specimen not found")
    data = specimen.to_dict()
    data["containers"] = [c.to_dict() for c in LimsContainer.query.filter_by(specimen_id=specimen.id).all()]
    data["history"] = [
        h.to_dict()
        for h in LimsSampleStatusHistory.query.filter_by(specimen_id=specimen.id)
        .order_by(LimsSampleStatusHistory.transitioned_at.asc())
        .all()
    ]
    accession = LimsAccession.query.filter_by(specimen_id=specimen.id).first()
    data["accession"] = accession.to_dict() if accession else None
    return data


def list_specimens(
    *,
    page: int = 1,
    per_page: int = 25,
    status: str | None = None,
    order_code: str | None = None,
    patient_code: str | None = None,
    organization_id: str | None = None,
) -> dict:
    query = LimsSpecimen.query
    if status:
        query = query.filter_by(status=status)
    if order_code:
        query = query.filter_by(order_code=order_code)
    if patient_code:
        query = query.filter_by(patient_code=patient_code)
    if organization_id:
        query = query.filter_by(organization_id=organization_id)

    total = query.count()
    rows = (
        query.order_by(LimsSpecimen.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    return {
        "items": [r.to_dict() for r in rows],
        "pagination": {"page": page, "per_page": per_page, "total": total},
    }


def update_specimen(specimen_id: str, *, patch: dict, actor: str | None = None) -> dict:
    specimen = LimsSpecimen.query.get(specimen_id)
    if not specimen:
        raise LimsCoreError("Specimen not found")
    if specimen.status == LIMS_SPECIMEN_ARCHIVED:
        raise LimsCoreError("Archived specimens cannot be modified")

    for field in ("container_type", "volume", "volume_unit", "patient_code", "order_code"):
        if field in patch and patch[field] is not None:
            if field == "container_type" and patch[field] not in LIMS_CONTAINER_TYPES:
                raise LimsCoreError(f"Invalid container_type: {patch[field]}")
            setattr(specimen, field, patch[field])
    specimen.updated_at = _utcnow()
    write_lims_audit(action="specimen_updated", object_type="specimen", object_id=specimen.id, actor=actor)
    return specimen.to_dict()


def verify_barcode(barcode_value: str) -> dict:
    log = LimsBarcodeLog.query.filter(
        (LimsBarcodeLog.barcode_value == barcode_value) | (LimsBarcodeLog.human_readable == barcode_value)
    ).first()
    if not log:
        specimen = LimsSpecimen.query.filter(
            (LimsSpecimen.barcode == barcode_value) | (LimsSpecimen.human_readable == barcode_value)
        ).first()
        if not specimen:
            raise LimsCoreError("Barcode not found")
        return {"valid": True, "specimen": specimen.to_dict()}
    specimen = LimsSpecimen.query.get(log.specimen_id) if log.specimen_id else None
    return {"valid": True, "barcode": log.to_dict(), "specimen": specimen.to_dict() if specimen else None}


def next_accession_number() -> str:
    today = _utcnow().strftime("%Y%m%d")
    prefix = f"LIMS-ACC-{today}-"
    last = (
        LimsAccession.query.filter(LimsAccession.accession_number.like(f"{prefix}%"))
        .order_by(LimsAccession.accession_number.desc())
        .first()
    )
    seq = 1
    if last:
        try:
            seq = int(last.accession_number.split("-")[-1]) + 1
        except ValueError:
            seq = 1
    return f"{prefix}{seq:06d}"


def receive_and_accession_specimen(
    *,
    barcode_value: str,
    operator: str,
    rack: str | None = None,
    shelf: str | None = None,
    batch: str | None = None,
    storage_location_id: str | None = None,
    laboratory_id: str | None = None,
    actor: str | None = None,
) -> dict:
    """Verify barcode, receive specimen, assign storage, create accession record."""
    verified = verify_barcode(barcode_value)
    specimen_data = verified.get("specimen")
    if not specimen_data:
        raise LimsCoreError("No specimen linked to barcode")

    specimen = LimsSpecimen.query.get(specimen_data["id"])
    if not specimen:
        raise LimsCoreError("Specimen not found")

    existing = LimsAccession.query.filter_by(specimen_id=specimen.id).first()
    if existing:
        result = existing.to_dict()
        result["specimen"] = specimen.to_dict()
        return result

    if specimen.status == LIMS_SPECIMEN_CREATED:
        transition_specimen(specimen.id, to_status=LIMS_SPECIMEN_COLLECTED, actor=actor, note="Received at lab")
        specimen = LimsSpecimen.query.get(specimen.id)
    if specimen.status == LIMS_SPECIMEN_COLLECTED:
        transition_specimen(specimen.id, to_status=LIMS_SPECIMEN_IN_TRANSIT, actor=actor)
        specimen = LimsSpecimen.query.get(specimen.id)
    if specimen.status == LIMS_SPECIMEN_IN_TRANSIT:
        transition_specimen(specimen.id, to_status=LIMS_SPECIMEN_RECEIVED, actor=actor, note="Specimen received")
        specimen = LimsSpecimen.query.get(specimen.id)
    if specimen.status == LIMS_SPECIMEN_RECEIVED:
        transition_specimen(specimen.id, to_status=LIMS_SPECIMEN_ACCESSIONED, actor=actor, note="Accessioned")
        specimen = LimsSpecimen.query.get(specimen.id)

    location = None
    if storage_location_id:
        location = LimsStorageLocation.query.get(storage_location_id)
    elif rack or shelf or batch:
        loc_code = f"{rack or 'R0'}-{shelf or 'S0'}-{batch or 'B0'}"
        location = LimsStorageLocation.query.filter_by(location_code=loc_code).first()
        if not location:
            location = LimsStorageLocation(
                location_code=loc_code,
                rack=rack,
                shelf=shelf,
                batch=batch,
                laboratory_id=laboratory_id,
            )
            db.session.add(location)
            db.session.flush()

    acc_num = next_accession_number()
    accession = LimsAccession(
        accession_number=acc_num,
        specimen_id=specimen.id,
        storage_location_id=location.id if location else None,
        rack=rack,
        shelf=shelf,
        batch=batch,
        operator=operator,
        accessioned_at=_utcnow(),
    )
    db.session.add(accession)
    write_lims_audit(action="accession_created", object_type="accession", object_id=acc_num, actor=actor)

    result = accession.to_dict()
    result["specimen"] = specimen.to_dict()
    result["storage_location"] = location.to_dict() if location else None
    return result


def list_accessions(*, page: int = 1, per_page: int = 25) -> dict:
    query = LimsAccession.query
    total = query.count()
    rows = (
        query.order_by(LimsAccession.accessioned_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    return {
        "items": [r.to_dict() for r in rows],
        "pagination": {"page": page, "per_page": per_page, "total": total},
    }


def get_accession(accession_id: str) -> dict:
    accession = LimsAccession.query.get(accession_id)
    if not accession:
        raise LimsCoreError("Accession not found")
    data = accession.to_dict()
    data["specimen"] = get_specimen(accession.specimen_id)
    if accession.storage_location_id:
        loc = LimsStorageLocation.query.get(accession.storage_location_id)
        data["storage_location"] = loc.to_dict() if loc else None
    return data


def lims_dashboard(*, organization_id: str | None = None) -> dict[str, Any]:
    """Realtime KPI dashboard for LIMS Core."""
    today = _utcnow().date()
    base = LimsSpecimen.query
    if organization_id:
        base = base.filter_by(organization_id=organization_id)

    samples_today = base.filter(func.date(LimsSpecimen.created_at) == today).count()
    pending_collection = base.filter(LimsSpecimen.status == LIMS_SPECIMEN_CREATED).count()
    in_transit = base.filter(LimsSpecimen.status == LIMS_SPECIMEN_IN_TRANSIT).count()
    received = base.filter(LimsSpecimen.status == LIMS_SPECIMEN_RECEIVED).count()
    processing = base.filter(LimsSpecimen.status == LIMS_SPECIMEN_PROCESSING).count()
    qc_failed = (
        db.session.query(LimsSampleStatusHistory)
        .join(LimsSpecimen, LimsSpecimen.id == LimsSampleStatusHistory.specimen_id)
        .filter(LimsSampleStatusHistory.note.isnot(None))
        .filter(LimsSampleStatusHistory.note.contains("fail"))
        .count()
    )
    validation_pending = base.filter(LimsSpecimen.status == LIMS_SPECIMEN_VALIDATING).count()
    released_today = base.filter(
        LimsSpecimen.status == LIMS_SPECIMEN_REPORTED,
        func.date(LimsSpecimen.updated_at) == today,
    ).count()

    return {
        "generated_at": _utcnow().isoformat(),
        "kpis": {
            "samples_today": samples_today,
            "pending_collection": pending_collection,
            "in_transit": in_transit,
            "received": received,
            "processing": processing,
            "qc_failed": qc_failed,
            "validation_pending": validation_pending,
            "released_today": released_today,
        },
        "cards": [
            {"label": "Samples Today", "value": samples_today},
            {"label": "Pending Collection", "value": pending_collection},
            {"label": "In Transit", "value": in_transit},
            {"label": "Received", "value": received},
            {"label": "Processing", "value": processing},
            {"label": "QC Failed", "value": qc_failed},
            {"label": "Validation Pending", "value": validation_pending},
            {"label": "Released Today", "value": released_today},
        ],
    }


def specimen_timeline(specimen_id: str) -> list[dict]:
    specimen = LimsSpecimen.query.get(specimen_id)
    if not specimen:
        raise LimsCoreError("Specimen not found")
    return [
        h.to_dict()
        for h in LimsSampleStatusHistory.query.filter_by(specimen_id=specimen_id)
        .order_by(LimsSampleStatusHistory.transitioned_at.asc())
        .all()
    ]
