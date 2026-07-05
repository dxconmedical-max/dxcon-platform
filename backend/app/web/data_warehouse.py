"""Data Warehouse web routes — Phase 7.7."""

from __future__ import annotations

from flask import Blueprint

from app.services.data_warehouse_service import DATA_WAREHOUSE_ROLES
from app.utils.auth import role_required
from app.web.data_warehouse_lib import (
    build_dashboard_body,
    build_etl_layer_body,
    build_fact_tables_body,
    build_dimension_tables_body,
    build_analytics_api_body,
    build_bi_export_body,
    build_powerbi_export_body,
    render_hub_page,
)

data_warehouse_web_bp = Blueprint("data_warehouse_web", __name__)

@data_warehouse_web_bp.route("/data-warehouse")
@role_required(*DATA_WAREHOUSE_ROLES)
def data_warehouse_dashboard():
    return render_hub_page("Data Warehouse", build_dashboard_body())
@data_warehouse_web_bp.route("/data-warehouse/etl")
@role_required(*DATA_WAREHOUSE_ROLES)
def data_warehouse_etl_layer():
    return render_hub_page("ETL Layer", build_etl_layer_body())
@data_warehouse_web_bp.route("/data-warehouse/facts")
@role_required(*DATA_WAREHOUSE_ROLES)
def data_warehouse_fact_tables():
    return render_hub_page("Fact Tables", build_fact_tables_body())
@data_warehouse_web_bp.route("/data-warehouse/dimensions")
@role_required(*DATA_WAREHOUSE_ROLES)
def data_warehouse_dimension_tables():
    return render_hub_page("Dimension Tables", build_dimension_tables_body())
@data_warehouse_web_bp.route("/data-warehouse/analytics")
@role_required(*DATA_WAREHOUSE_ROLES)
def data_warehouse_analytics_api():
    return render_hub_page("Analytics API", build_analytics_api_body())
@data_warehouse_web_bp.route("/data-warehouse/bi-export")
@role_required(*DATA_WAREHOUSE_ROLES)
def data_warehouse_bi_export():
    return render_hub_page("BI Export", build_bi_export_body())
@data_warehouse_web_bp.route("/data-warehouse/powerbi")
@role_required(*DATA_WAREHOUSE_ROLES)
def data_warehouse_powerbi_export():
    return render_hub_page("PowerBI Export", build_powerbi_export_body())

