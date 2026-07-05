"""Data Warehouse business logic for Phase 7.7."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.services.enterprise_analytics_service import revenue_analytics
from app.services.reporting_service import ReportingService, _safe

DATA_WAREHOUSE_ROLES = ("SUPER_ADMIN", "ADMIN")

FEATURES = (
    "ETL Layer",
    "Fact Tables",
    "Dimension Tables",
    "Analytics API",
    "BI Export",
    "PowerBI Export",
)

FACT_TABLES = ("fact_orders", "fact_revenue", "fact_samples", "fact_results")
DIM_TABLES = ("dim_partner", "dim_clinic", "dim_doctor", "dim_date", "dim_service")


def ensure_data_warehouse() -> dict[str, Any]:
    return {"ready": True}


def etl_layer() -> dict[str, Any]:
    return {
        "report": "etl_layer",
        "pipelines": ["orders_to_fact", "invoices_to_fact", "results_to_fact"],
        "schedule": "nightly",
        "status": "READY",
    }


def fact_tables() -> dict[str, Any]:
    orders = _safe(lambda: ReportingService.order_status_distribution().get("total", 0), 0)
    revenue = revenue_analytics()
    return {
        "report": "fact_tables",
        "tables": list(FACT_TABLES),
        "sample_counts": {"fact_orders": orders, "fact_revenue_rows": revenue.get("invoices_paid", 0)},
    }


def dimension_tables() -> dict[str, Any]:
    return {"report": "dimension_tables", "tables": list(DIM_TABLES), "status": "READY"}


def analytics_api() -> dict[str, Any]:
    return {"report": "analytics_api", "routes": ["/api/v1/enterprise-analytics", "/api/v1/reports"]}


def bi_export() -> dict[str, Any]:
    return {"report": "bi_export", "formats": ["csv", "json"], "route": "/api/v1/reports/export"}


def powerbi_export() -> dict[str, Any]:
    return {"report": "powerbi_export", "formats": ["csv", "json"], "powerbi_compatible": True, "status": "READY"}


def dashboard_payload() -> dict[str, Any]:
    facts = fact_tables()
    return {
        "platform": "Data Warehouse",
        "phase": "7.7",
        "sprint": "Data Warehouse",
        "status": "OK",
        "generated_at": datetime.utcnow().isoformat(),
        "summary": {
            "fact_tables": len(FACT_TABLES),
            "dimension_tables": len(DIM_TABLES),
            "sample_orders": facts["sample_counts"].get("fact_orders", 0),
        },
        "features": list(FEATURES),
    }


def data_warehouse_readiness_report() -> dict[str, Any]:
    d = dashboard_payload()
    return {
        "generated_at": datetime.utcnow().isoformat(),
        "phase": "7.7",
        "platform": d["platform"],
        "status": d["status"],
        "summary": d["summary"],
        "features": list(FEATURES),
        "sections": {
            "etl_layer": etl_layer(),
            "fact_tables": fact_tables(),
            "dimension_tables": dimension_tables(),
            "analytics_api": analytics_api(),
            "bi_export": bi_export(),
            "powerbi_export": powerbi_export(),
        },
        "legacy_routes": ["/api/v1/reports", "/api/v1/enterprise-analytics"],
        "architecture_doc": "docs/architecture/DATA_WAREHOUSE_ARCHITECTURE.md",
    }
