"""Data Warehouse API routes — Phase 7.7."""

from __future__ import annotations

from flask import Blueprint

from app.services.data_warehouse_service import (
    dashboard_payload,
    etl_layer,
    fact_tables,
    dimension_tables,
    analytics_api,
    bi_export,
    powerbi_export,
    data_warehouse_readiness_report,
)

data_warehouse_bp = Blueprint("data_warehouse_api", __name__, url_prefix="/api/v1/data-warehouse")

@data_warehouse_bp.route("/dashboard", methods=["GET"])
def data_warehouse_dashboard_api():
    return dashboard_payload()

@data_warehouse_bp.route("/etl", methods=["GET"])
def data_warehouse_etl_layer_api():
    return etl_layer()

@data_warehouse_bp.route("/facts", methods=["GET"])
def data_warehouse_fact_tables_api():
    return fact_tables()

@data_warehouse_bp.route("/dimensions", methods=["GET"])
def data_warehouse_dimension_tables_api():
    return dimension_tables()

@data_warehouse_bp.route("/analytics", methods=["GET"])
def data_warehouse_analytics_api_api():
    return analytics_api()

@data_warehouse_bp.route("/bi-export", methods=["GET"])
def data_warehouse_bi_export_api():
    return bi_export()

@data_warehouse_bp.route("/powerbi", methods=["GET"])
def data_warehouse_powerbi_export_api():
    return powerbi_export()

@data_warehouse_bp.route("/readiness", methods=["GET"])
def data_warehouse_readiness_api():
    return data_warehouse_readiness_report()
