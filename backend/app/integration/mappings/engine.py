"""Mapping engine — Epic 3.5."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.extensions.db import db
from app.integration.models import IntgMappingRule


def apply_mapping_rules(connector_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    rules = IntgMappingRule.query.filter_by(connector_id=connector_id, is_active=True).all()
    if not rules:
        return payload.copy()
    mapped: dict[str, Any] = {}
    for rule in rules:
        value = payload.get(rule.external_field)
        if value is None and rule.default_value is not None:
            value = rule.default_value
        if rule.transformation_type == "DATE_FORMAT" and value and rule.date_format:
            try:
                value = datetime.strptime(str(value), rule.date_format).isoformat()
            except ValueError:
                pass
        if value is not None:
            mapped[rule.canonical_field] = value
    for key, value in payload.items():
        mapped.setdefault(key, value)
    return mapped


def preview_mapping(connector_id: str, sample: dict[str, Any]) -> dict[str, Any]:
    return {
        "input": sample,
        "output": apply_mapping_rules(connector_id, sample),
    }


def upsert_mapping_rule(data: dict[str, Any], *, organization_id: str) -> dict:
    connector_id = data.get("connector_id")
    ext = data.get("external_field")
    canonical = data.get("canonical_field")
    if not connector_id or not ext or not canonical:
        raise ValueError("connector_id, external_field, canonical_field required")
    row = IntgMappingRule.query.filter_by(connector_id=connector_id, external_field=ext).first()
    if not row:
        row = IntgMappingRule(
            connector_id=connector_id,
            organization_id=organization_id,
            external_field=ext,
            canonical_field=canonical,
        )
        db.session.add(row)
    row.canonical_field = canonical
    row.transformation_type = data.get("transformation_type", "DIRECT")
    row.default_value = data.get("default_value")
    row.required = bool(data.get("required", False))
    row.date_format = data.get("date_format")
    row.is_active = bool(data.get("is_active", True))
    db.session.flush()
    return row.to_dict()
