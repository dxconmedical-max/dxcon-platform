"""Introspect live database schema and resolve primary keys for ORM compatibility."""

from __future__ import annotations

from typing import Any

from sqlalchemy import inspect as sa_inspect

from app.extensions.db import db

SEED_MODEL_SPECS: tuple[tuple[str, str, str], ...] = (
    ("User", "app.models.user", "users"),
    ("Patient", "app.models.patient", "patients"),
    ("PatientProfile", "app.models.patient_profile", "patient_profiles"),
    ("Laboratory", "app.models.laboratory", "laboratories"),
    ("Partner", "app.models.partner", "partners"),
    ("DoctorProfile", "app.models.doctor_profile", "doctor_profiles"),
    ("Company", "app.models.company", "companies"),
    ("TestCatalog", "app.models.test_catalog", "test_catalogs"),
    ("Order", "app.models.order", "orders"),
    ("OrderItem", "app.models.order_item", "order_items"),
    ("SampleCollection", "app.models.sample_collection", "sample_collections"),
    ("Driver", "app.models.driver", "drivers"),
    ("Shipment", "app.models.shipment", "shipments"),
    ("Invoice", "app.models.invoice", "invoices"),
    ("Notification", "app.models.notification", "notifications"),
)

MODEL_SYNC_CHANGES: tuple[dict[str, Any], ...] = (
    {
        "model": "Patient",
        "table": "patients",
        "change": "primary_key",
        "from": "id",
        "to": "patient_code",
        "reason": "Production PostgreSQL uses patient_code as patients PK; id column absent.",
    },
    {
        "model": "PatientProfile",
        "table": "patient_profiles",
        "change": "foreign_key",
        "from": "patients.id",
        "to": "patients.patient_code",
        "reason": "Align patient_profiles.patient_id FK with patients primary key.",
    },
    {
        "model": "PatientConsent",
        "table": "patient_consents",
        "change": "foreign_key",
        "from": "patients.id",
        "to": "patients.patient_code",
        "reason": "Patient FK target follows patients.patient_code PK.",
    },
    {
        "model": "PatientPreference",
        "table": "patient_preferences",
        "change": "foreign_key",
        "from": "patients.id",
        "to": "patients.patient_code",
        "reason": "Patient FK target follows patients.patient_code PK.",
    },
    {
        "model": "PatientNotificationSetting",
        "table": "patient_notification_settings",
        "change": "foreign_key",
        "from": "patients.id",
        "to": "patients.patient_code",
        "reason": "Patient FK target follows patients.patient_code PK.",
    },
    {
        "model": "PatientDevice",
        "table": "patient_devices",
        "change": "foreign_key",
        "from": "patients.id",
        "to": "patients.patient_code",
        "reason": "Patient FK target follows patients.patient_code PK.",
    },
    {
        "model": "DoctorPatient",
        "table": "doctor_patients",
        "change": "foreign_key",
        "from": "patients.id",
        "to": "patients.patient_code",
        "reason": "Patient FK target follows patients.patient_code PK.",
    },
    {
        "model": "DoctorFollowUp",
        "table": "doctor_follow_ups",
        "change": "foreign_key",
        "from": "patients.id",
        "to": "patients.patient_code",
        "reason": "Patient FK target follows patients.patient_code PK.",
    },
    {
        "model": "DoctorReferral",
        "table": "doctor_referrals",
        "change": "foreign_key",
        "from": "patients.id",
        "to": "patients.patient_code",
        "reason": "Patient FK target follows patients.patient_code PK.",
    },
    {
        "model": "DoctorNote",
        "table": "doctor_notes",
        "change": "foreign_key",
        "from": "patients.id",
        "to": "patients.patient_code",
        "reason": "Patient FK target follows patients.patient_code PK.",
    },
    {
        "model": "ClinicPatient",
        "table": "clinic_patients",
        "change": "foreign_key",
        "from": "patients.id",
        "to": "patients.patient_code",
        "reason": "Patient FK target follows patients.patient_code PK.",
    },
    {
        "model": "ClinicBooking",
        "table": "clinic_bookings",
        "change": "foreign_key",
        "from": "patients.id",
        "to": "patients.patient_code",
        "reason": "Patient FK target follows patients.patient_code PK.",
    },
    {
        "model": "ClinicOrder",
        "table": "clinic_orders",
        "change": "foreign_key",
        "from": "patients.id",
        "to": "patients.patient_code",
        "reason": "Patient FK target follows patients.patient_code PK.",
    },
    {
        "model": "ClinicReferral",
        "table": "clinic_referrals",
        "change": "foreign_key",
        "from": "patients.id",
        "to": "patients.patient_code",
        "reason": "Patient FK target follows patients.patient_code PK.",
    },
)


def _inspector():
    # Prefer the active session bind so sqlite :memory: / StaticPool checks
    # do not checkout a separate connection and invalidate an open transaction.
    try:
        bind = db.session.get_bind()
        if bind is not None:
            return sa_inspect(bind)
    except Exception:
        pass
    return sa_inspect(db.engine)


def table_exists_name(table_name: str) -> bool:
    """Return True if table exists, using the active session when possible.

    Engine-level inspection can steal the StaticPool sqlite connection and
    drop visibility of uncommitted rows in the current request transaction.
    """
    try:
        bind = db.session.get_bind()
        if bind is not None and bind.dialect.name == "sqlite":
            row = db.session.execute(
                db.text(
                    "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = :name LIMIT 1"
                ),
                {"name": table_name},
            ).first()
            return row is not None
        return table_name in _inspector().get_table_names()
    except Exception:
        return False


def get_table_columns(table_name: str) -> set[str]:
    try:
        bind = db.session.get_bind()
        if bind is not None and bind.dialect.name == "sqlite":
            rows = db.session.execute(db.text(f"PRAGMA table_info({table_name})")).fetchall()
            return {row[1] for row in rows}
        inspector = _inspector()
        if table_name not in inspector.get_table_names():
            return set()
        return {column["name"] for column in inspector.get_columns(table_name)}
    except Exception:
        return set()


def columns_exist(table_name: str, *column_names: str) -> bool:
    columns = get_table_columns(table_name)
    return bool(columns) and all(name in columns for name in column_names)


def get_table_primary_key(table_name: str) -> list[str]:
    try:
        if not table_exists_name(table_name):
            return []
        pk = _inspector().get_pk_constraint(table_name) or {}
        return list(pk.get("constrained_columns") or [])
    except Exception:
        return []


def get_table_foreign_keys(table_name: str) -> list[dict[str, Any]]:
    try:
        if not table_exists_name(table_name):
            return []
        return _inspector().get_foreign_keys(table_name) or []
    except Exception:
        return []


def fk_target_compatible(source_table: str, fk_column: str, target_table: str, target_column: str) -> bool:
    if not table_exists_name(source_table) or not table_exists_name(target_table):
        return False
    source_columns = get_table_columns(source_table)
    target_columns = get_table_columns(target_table)
    return fk_column in source_columns and target_column in target_columns


def model_primary_key_columns(model) -> list[str]:
    return [column.name for column in model.__table__.primary_key.columns]


def model_pk_value(instance) -> Any:
    pks = model_primary_key_columns(instance)
    if len(pks) == 1:
        return getattr(instance, pks[0])
    if not pks:
        return None
    return tuple(getattr(instance, name) for name in pks)


def patient_reference_column(table_columns: set[str] | None = None) -> str | None:
    columns = table_columns if table_columns is not None else get_table_columns("patients")
    db_pk = get_table_primary_key("patients")
    if db_pk:
        return db_pk[0]
    if "id" in columns:
        return "id"
    if "patient_code" in columns:
        return "patient_code"
    return None


def import_model(module_path: str, class_name: str):
    import importlib

    try:
        module = importlib.import_module(module_path)
        return getattr(module, class_name), None
    except (ImportError, AttributeError):
        return None, "model_not_found"


def compare_model_to_database(model) -> dict[str, Any]:
    table_name = model.__tablename__
    db_columns = get_table_columns(table_name)
    model_columns = {column.name for column in model.__table__.columns}
    model_pks = model_primary_key_columns(model)
    db_pks = get_table_primary_key(table_name)

    missing_in_db = sorted(model_columns - db_columns) if db_columns else sorted(model_columns)
    missing_in_model = sorted(db_columns - model_columns) if db_columns else []
    pk_match = model_pks == db_pks if db_columns else None

    fk_issues: list[str] = []
    for fk in model.__table__.foreign_keys:
        target_table = fk.column.table.name
        target_column = fk.column.name
        local_column = fk.parent.name
        if db_columns and not fk_target_compatible(table_name, local_column, target_table, target_column):
            fk_issues.append(f"{local_column}->{target_table}.{target_column}")

    return {
        "table": table_name,
        "table_exists": table_exists_name(table_name),
        "model_primary_key": model_pks,
        "database_primary_key": db_pks,
        "primary_key_match": pk_match,
        "model_columns": sorted(model_columns),
        "database_columns": sorted(db_columns),
        "model_columns_missing_in_db": missing_in_db,
        "database_columns_missing_in_model": missing_in_model,
        "foreign_key_issues": fk_issues,
        "compatible": bool(db_columns)
        and not missing_in_db
        and pk_match is not False
        and not fk_issues,
    }


def inspect_seed_schema() -> dict[str, Any]:
    schema: dict[str, Any] = {"tables": {}, "warnings": []}
    for table_name in ("patients", "patient_profiles", "orders", "laboratories", "test_catalogs"):
        if not table_exists_name(table_name):
            continue
        columns = sorted(get_table_columns(table_name))
        schema["tables"][table_name] = {
            "columns": columns,
            "primary_key": get_table_primary_key(table_name),
            "has_id": "id" in columns,
            "has_patient_code": "patient_code" in columns,
        }
    patient_pk = get_table_primary_key("patients")
    profile_fks = get_table_foreign_keys("patient_profiles")
    if table_exists_name("patient_profiles"):
        for fk in profile_fks:
            if fk.get("referred_table") == "patients" and fk.get("referred_columns") != patient_pk:
                schema["warnings"].append(
                    "patient_profiles FK targets "
                    f"{fk.get('referred_columns')} but patients PK is {patient_pk}"
                )
    if patient_pk == ["patient_code"]:
        schema["warnings"].append("patients primary key is patient_code (legacy/production schema)")
    return schema


def build_schema_compatibility_report() -> dict[str, Any]:
    from datetime import datetime, timezone

    models: list[dict[str, Any]] = []
    for class_name, module_path, _table in SEED_MODEL_SPECS:
        model, reason = import_model(module_path, class_name)
        if model is None:
            models.append(
                {
                    "model": class_name,
                    "module": module_path,
                    "import_error": reason,
                    "compatible": False,
                }
            )
            continue
        entry = compare_model_to_database(model)
        entry["model"] = class_name
        entry["module"] = module_path
        models.append(entry)

    changed_models = [item for item in MODEL_SYNC_CHANGES]
    compatible_count = sum(1 for item in models if item.get("compatible"))
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "seed_models_checked": len(models),
            "compatible_models": compatible_count,
            "incompatible_models": len(models) - compatible_count,
            "models_changed_for_production_schema": len(changed_models),
        },
        "changed_models": changed_models,
        "models": models,
        "database": str(db.engine.url).split("@")[-1] if db.engine else "unknown",
    }
