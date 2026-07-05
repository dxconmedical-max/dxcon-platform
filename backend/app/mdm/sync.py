"""Sync MDM golden records to legacy operational tables (backward compatibility)."""

from __future__ import annotations

import uuid
from datetime import datetime

from app.extensions.db import db
from app.mdm.registry import ENTITY_SCHEMAS
from app.models.mdm import MdmMasterRecord, MDM_ACTIVE


def sync_record_to_legacy(record: MdmMasterRecord) -> bool:
    """Upsert legacy table row when configured. Returns True if synced."""
    if record.status != MDM_ACTIVE:
        return False
    try:
        with db.session.begin_nested():
            return _sync_record_to_legacy_inner(record)
    except Exception:
        return False


def _sync_record_to_legacy_inner(record: MdmMasterRecord) -> bool:
    schema = ENTITY_SCHEMAS.get(record.entity_type, {})
    legacy = schema.get("legacy_sync")
    if not legacy:
        return False

    attrs = record.attributes()
    code = record.code
    name = record.name

    if legacy == "test_catalogs":
        from app.models.test_catalog import TestCatalog

        row = TestCatalog.query.filter_by(code=code).first()
        if not row:
            row = TestCatalog(id=str(uuid.uuid4()), code=code, name=name)
            db.session.add(row)
        row.name = name
        row.category = attrs.get("category") or row.category
        row.sample_type = attrs.get("sample_type") or row.sample_type
        try:
            row.price = float(attrs.get("price") or row.price or 0)
        except (TypeError, ValueError):
            pass
        return True

    if legacy == "laboratories":
        from app.models.laboratory import Laboratory

        row = Laboratory.query.filter_by(code=code).first() if hasattr(Laboratory, "code") else None
        if row is None:
            row = Laboratory.query.filter_by(name=name).first()
        if not row:
            row = Laboratory(
                id=str(uuid.uuid4()),
                name=name,
            )
            if hasattr(row, "code"):
                row.code = code
            db.session.add(row)
        row.name = name
        if hasattr(row, "address"):
            row.address = attrs.get("address") or getattr(row, "address", None)
        if hasattr(row, "phone"):
            row.phone = attrs.get("phone") or getattr(row, "phone", None)
        return True

    if legacy == "payment_methods":
        from app.models.payment_method import PaymentMethod

        row = PaymentMethod.query.filter_by(code=code).first() if hasattr(PaymentMethod, "code") else None
        if not row:
            row = PaymentMethod(
                id=str(uuid.uuid4()),
                name=name,
            )
            if hasattr(row, "code"):
                row.code = code
            db.session.add(row)
        row.name = name
        return True

    if legacy == "reference_ranges":
        from app.models.reference_range import ReferenceRange

        row = ReferenceRange.query.filter_by(code=code).first() if hasattr(ReferenceRange, "code") else None
        if not row:
            row = ReferenceRange(id=str(uuid.uuid4()))
            if hasattr(row, "code"):
                row.code = code
            db.session.add(row)
        if hasattr(row, "test_code"):
            row.test_code = attrs.get("test_code") or getattr(row, "test_code", None)
        if hasattr(row, "name"):
            row.name = name
        return True

    if legacy == "notification_templates":
        from app.models.notification_template import NotificationTemplate

        row = NotificationTemplate.query.filter_by(template_code=code).first() if hasattr(NotificationTemplate, "template_code") else None
        if not row:
            row = NotificationTemplate(
                id=str(uuid.uuid4()),
                template_code=code,
                name=name,
            )
            db.session.add(row)
        row.name = name
        if hasattr(row, "channel"):
            row.channel = attrs.get("channel") or getattr(row, "channel", None)
        if hasattr(row, "body"):
            row.body = attrs.get("body_template") or getattr(row, "body", None)
        return True

    if legacy == "contracts":
        from app.models.contract import Contract

        row = Contract.query.filter_by(contract_code=code).first() if hasattr(Contract, "contract_code") else None
        if not row:
            row = Contract(
                id=str(uuid.uuid4()),
                contract_code=code,
                name=name,
            )
            db.session.add(row)
        row.name = name
        return True

    if legacy == "standard_codes":
        from app.models.healthcare_standards import StandardCode, StandardCodeSystem

        system_code = schema.get("standard_system", "LOINC")
        system = StandardCodeSystem.query.filter_by(system_code=system_code).first()
        if not system:
            system = StandardCodeSystem(
                system_code=system_code,
                name=system_code,
                version="2026",
            )
            db.session.add(system)
            db.session.flush()
        row = StandardCode.query.filter_by(system_id=system.id, code=code).first()
        if not row:
            row = StandardCode(system_id=system.id, code=code, display=name)
            db.session.add(row)
        row.display = name
        row.category = attrs.get("category") or row.category
        return True

    if legacy == "doctor_profiles":
        from app.models.doctor_profile import DoctorProfile

        row = DoctorProfile.query.filter_by(doctor_code=code).first()
        if not row:
            row = DoctorProfile(
                doctor_id=str(uuid.uuid4()),
                doctor_code=code,
                full_name=name,
            )
            db.session.add(row)
        row.full_name = name
        row.specialty_primary = attrs.get("specialty") or row.specialty_primary
        row.license_number = attrs.get("license_number") or row.license_number
        row.phone = attrs.get("phone") or row.phone
        row.email = attrs.get("email") or row.email
        return True

    if legacy == "clinic_profiles":
        from app.models.clinic_profile import ClinicProfile

        row = ClinicProfile.query.filter_by(clinic_code=code).first()
        if not row:
            row = ClinicProfile(
                clinic_id=str(uuid.uuid4()),
                clinic_code=code,
                name=name,
            )
            db.session.add(row)
        row.name = name
        row.address = attrs.get("address") or row.address
        row.phone = attrs.get("phone") or row.phone
        row.email = attrs.get("email") or row.email
        if attrs.get("tenant_id"):
            row.tenant_id = attrs.get("tenant_id")
        return True

    if legacy == "lab_analyzers":
        from app.models.lab_facility import Analyzer

        row = Analyzer.query.filter_by(analyzer_code=code).first()
        if not row:
            row = Analyzer(analyzer_code=code, name=name)
            db.session.add(row)
        row.name = name
        row.manufacturer = attrs.get("manufacturer") or row.manufacturer
        row.model = attrs.get("model") or row.model
        if attrs.get("status"):
            row.status = attrs.get("status").upper()
        return True

    return False


def deactivate_legacy(record: MdmMasterRecord) -> None:
    """Best-effort legacy deactivation on rollback — non-destructive (status only where supported)."""
    schema = ENTITY_SCHEMAS.get(record.entity_type, {})
    legacy = schema.get("legacy_sync")
    if not legacy:
        return
    code = record.code
    if legacy == "test_catalogs":
        from app.models.test_catalog import TestCatalog

        row = TestCatalog.query.filter_by(code=code).first()
        if row and hasattr(row, "status"):
            row.status = "inactive"
