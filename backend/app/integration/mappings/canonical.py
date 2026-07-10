"""Canonical healthcare payloads — Epic 3.5."""

from __future__ import annotations

from typing import Any

CANONICAL_PATIENT_FIELDS = (
    "patient_code", "full_name", "date_of_birth", "gender", "phone",
    "national_id", "address", "organization_id",
)

CANONICAL_ORDER_FIELDS = (
    "order_code", "patient_code", "ordering_doctor_code", "clinic_code",
    "laboratory_code", "tests", "priority", "ordered_at", "collection_type",
)

CANONICAL_SAMPLE_FIELDS = (
    "sample_code", "order_code", "sample_type", "tube_type",
    "collected_at", "received_at", "condition",
)

CANONICAL_RESULT_FIELDS = (
    "order_code", "sample_code", "test_code", "result_value", "result_text",
    "unit", "reference_range", "abnormal_flag", "result_time", "analyzer",
    "technician", "status",
)

CANONICAL_REPORT_FIELDS = (
    "report_code", "order_code", "version", "approved_at", "released_at",
    "report_url", "report_hash",
)


def validate_canonical(payload: dict[str, Any], fields: tuple[str, ...]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    for field in fields:
        if field.endswith("_id") or field in {"tests"}:
            continue
        if field in {"patient_code", "order_code", "test_code", "result_value"} and not payload.get(field):
            errors.append(f"missing {field}")
    return len(errors) == 0, errors


def to_canonical_result(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "order_code": raw.get("order_code") or raw.get("external_order_id"),
        "sample_code": raw.get("sample_code") or raw.get("external_sample_id"),
        "test_code": raw.get("test_code") or raw.get("external_test_code"),
        "result_value": raw.get("result_value") or raw.get("value"),
        "unit": raw.get("unit"),
        "reference_range": raw.get("reference_range"),
        "abnormal_flag": raw.get("abnormal_flag") or raw.get("flag"),
        "result_time": raw.get("result_time"),
        "analyzer": raw.get("analyzer") or raw.get("instrument"),
        "technician": raw.get("technician"),
        "status": "IMPORTED",
    }
