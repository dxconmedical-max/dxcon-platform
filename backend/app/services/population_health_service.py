"""Population Health business logic for Phase 7.8."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.models.knowledge_engine import DiseaseProfile
from app.services.reporting_service import _safe

POPULATION_HEALTH_ROLES = ("SUPER_ADMIN", "ADMIN")

FEATURES = (
    "Disease Registry",
    "Population Dashboard",
    "Risk Groups",
    "Vaccination Statistics",
    "Diabetes",
    "Hypertension",
    "Cancer",
    "Women's Health",
    "Children",
)

PANELS = {
    "diabetes_panel": {"code": "DM-T2", "name": "Diabetes", "markers": ["GLU", "HBA1C"]},
    "hypertension_panel": {"code": "HTN", "name": "Hypertension", "markers": ["BP_SYS", "BP_DIA"]},
    "cancer_panel": {"code": "CA-SCREEN", "name": "Cancer Screening", "markers": ["PSA", "CA125"]},
    "womens_health_panel": {"code": "WH", "name": "Women's Health", "markers": ["CA125", "TSH"]},
    "children_panel": {"code": "PED", "name": "Children", "markers": ["GLU", "HGB"]},
}


def ensure_population_health() -> dict[str, Any]:
    return {"ready": True}


def disease_registry() -> dict[str, Any]:
    rows = _safe(lambda: DiseaseProfile.query.all(), [])
    return {
        "report": "disease_registry",
        "count": len(rows),
        "diseases": [row.to_dict() for row in rows[:25]],
    }


def population_dashboard() -> dict[str, Any]:
    reg = disease_registry()
    return {
        "report": "population_dashboard",
        "diseases_tracked": reg["count"],
        "panels": len(PANELS),
        "status": "READY",
    }


def risk_groups() -> dict[str, Any]:
    return {
        "report": "risk_groups",
        "groups": [
            {"name": "High Risk Diabetes", "criteria": "HBA1C >= 6.5"},
            {"name": "Hypertension Stage 2", "criteria": "BP >= 140/90"},
        ],
    }


def vaccination_statistics() -> dict[str, Any]:
    return {
        "report": "vaccination_statistics",
        "coverage_percent": 78.5,
        "doses_administered": 12400,
        "status": "DEMO",
    }


def _panel(key: str) -> dict[str, Any]:
    panel = PANELS[key]
    return {"report": key, **panel, "mapping_available": True}


def diabetes_panel() -> dict[str, Any]:
    return _panel("diabetes_panel")


def hypertension_panel() -> dict[str, Any]:
    return _panel("hypertension_panel")


def cancer_panel() -> dict[str, Any]:
    return _panel("cancer_panel")


def womens_health_panel() -> dict[str, Any]:
    return _panel("womens_health_panel")


def children_panel() -> dict[str, Any]:
    return _panel("children_panel")


def dashboard_payload() -> dict[str, Any]:
    reg = disease_registry()
    return {
        "platform": "Population Health",
        "phase": "7.8",
        "sprint": "Population Health",
        "status": "OK",
        "generated_at": datetime.utcnow().isoformat(),
        "summary": {"diseases_tracked": reg["count"], "panels": len(PANELS)},
        "features": list(FEATURES),
    }


def population_health_readiness_report() -> dict[str, Any]:
    d = dashboard_payload()
    return {
        "generated_at": datetime.utcnow().isoformat(),
        "phase": "7.8",
        "platform": d["platform"],
        "status": d["status"],
        "summary": d["summary"],
        "features": list(FEATURES),
        "sections": {
            "disease_registry": disease_registry(),
            "population_dashboard": population_dashboard(),
            "risk_groups": risk_groups(),
            "vaccination_statistics": vaccination_statistics(),
            "diabetes": diabetes_panel(),
            "hypertension": hypertension_panel(),
            "cancer": cancer_panel(),
            "womens_health": womens_health_panel(),
            "children": children_panel(),
        },
        "legacy_routes": ["/api/v1/diseases", "/api/v1/knowledge"],
        "architecture_doc": "docs/architecture/POPULATION_HEALTH_ARCHITECTURE.md",
    }
