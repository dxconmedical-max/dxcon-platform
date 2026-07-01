from app.web.box_qr import box_qr_web_bp
from app.api.box_qr.routes import box_qr_bp
from app.web.logistics_v2 import logistics_v2_web_bp
from app.api.logistics_v2.routes import logistics_v2_bp
from app.web.shipments import shipments_web_bp
from app.api.shipments.routes import shipments_bp
from app.api.result_files.routes import result_files_bp
from app.web.monitor import monitor_web_bp
from app.api.system.routes import system_bp
from app.api.ai_v2.routes import ai_interpret_v2_bp
from app.api.security.routes import security_api_bp
from app.web.security import security_web_bp
from app.api.ops.routes import ops_bp
from app.web.home import home_web_bp
from app.web.executive_v9 import executive_v9_bp
from app.web.crm_v2 import crm_v2_web_bp
from app.web.finance import finance_web_bp
from flask import Flask, redirect

from app.core.config import Config
from app.core.config_validation import validate_config
from app.core.deployment import init_deployment
from app.core.jwt_auth import init_jwt_security
from app.core.observability import finalize_observability, init_observability
from app.core.performance import init_performance
from app.core.security import init_security

from app.extensions.db import db
from app.extensions.jwt import jwt

from app.models import *

from app.api.auth.routes import auth_bp
from app.api.admin.routes import admin_bp
from app.api.patients.routes import patients_bp
from app.api.laboratories.routes import laboratories_bp
from app.api.test_catalogs.routes import test_catalogs_bp
from app.api.orders.routes import orders_bp
from app.api.order_items.routes import order_items_bp
from app.api.sample_collections.routes import sample_collections_bp
from app.api.test_results.routes import test_results_bp
from app.api.companies.routes import companies_bp
from app.api.marketplace.routes import marketplace_bp
from app.api.partners.routes import partners_bp
from app.api.scheduling.routes import scheduling_bp
from app.api.order_lifecycle.routes import order_lifecycle_bp
from app.api.collector_operations.routes import collector_operations_bp
from app.api.order_execution.routes import order_execution_bp
from app.api.billing.routes import billing_bp
from app.api.partner_portal.routes import partner_portal_bp
from app.api.reporting.routes import reporting_bp
from app.api.results.routes import results_bp
from app.api.interpretation.routes import interpretation_bp, reference_ranges_bp
from app.api.notifications.routes import notifications_bp, notification_templates_bp
from app.api.patient_portal.routes import patient_portal_bp
from app.api.clinic_portal.routes import clinic_portal_bp
from app.api.doctor_portal.routes import doctor_portal_bp
from app.api.contracts.routes import contracts_bp
from app.api.contract_prices.routes import contract_prices_bp
from app.api.invoices.routes import invoices_bp
from app.api.payments.routes import payments_bp
from app.api.integrations.routes import integrations_bp
from app.api.iot.routes import iot_bp
from app.api.dashboard.routes import dashboard_bp
from app.api.seeds.routes import seeds_bp
from app.api.mobile.routes import mobile_bp
from app.api.workflow.routes import workflow_bp
from app.api.home_collections.routes import home_collections_bp
from app.api.sample_trackings.routes import sample_trackings_bp
from app.api.incidents.routes import incidents_bp
from app.api.admin_security.routes import admin_security_bp

from app.web.auth import auth_web_bp
from app.web.dashboard import dashboard_web_bp
from app.web.patients import patients_web_bp
from app.web.companies import companies_web_bp
from app.web.marketplace import marketplace_web_bp
from app.web.partners import partners_web_bp
from app.web.scheduling import scheduling_web_bp
from app.web.order_lifecycle import order_lifecycle_web_bp
from app.web.collector_operations import collector_operations_web_bp
from app.web.order_execution import order_execution_web_bp
from app.web.partner_portal_v2 import partner_portal_web_bp
from app.web.reporting_bi import reporting_bi_web_bp
from app.web.result_gateway import result_gateway_web_bp
from app.web.interpretation_admin import interpretation_admin_web_bp
from app.web.notifications_admin import notifications_admin_web_bp
from app.web.patient_portal_v2 import patient_portal_v2_web_bp
from app.web.clinic_portal_v2 import clinic_portal_v2_web_bp
from app.web.doctor_portal_v2 import doctor_portal_v2_web_bp
from app.web.billing_invoice_v2 import billing_invoice_web_bp
from app.web.payment_gateway_v2 import payment_gateway_web_bp
from app.web.integrations_v2 import integrations_web_bp
from app.web.iot_cold_chain_v2 import iot_web_bp
from app.web.contracts import contracts_web_bp
from app.web.orders import orders_web_bp
from app.web.invoices import invoices_web_bp
from app.web.payments import payments_web_bp
from app.web.order_items import order_items_web_bp
from app.web.test_results import test_results_web_bp
from app.web.reports import reports_web_bp
from app.web.report_pdf import report_pdf_web_bp
from app.web.patient_portal import patient_portal_web_bp
from app.web.doctor_portal import doctor_portal_web_bp
from app.web.home_collections import home_collections_web_bp
from app.web.collector_portal import collector_portal_web_bp
from app.web.sample_tracking import sample_tracking_web_bp
from app.web.result_upload import result_upload_web_bp

from app.api.transport_boxes.routes import transport_boxes_bp
from app.web.transport_boxes import transport_boxes_web_bp
from app.web.drivers import drivers_web_bp
from app.web.dispatch import dispatch_web_bp
from app.web.dispatch_optimizer import dispatch_optimizer_web_bp
from app.web.lab_worklist import lab_worklist_bp
from app.web.result_verify import result_verify_web_bp
from app.web.analytics import analytics_web_bp
from app.api.ai_cds.routes import ai_cds_bp
from app.api.ai.routes_v2 import ai_v2_bp
from app.api.alerts.routes import alerts_bp
from app.web.alerts import alerts_web_bp
from app.web.operations_timeline import operations_timeline_web_bp
from app.web.operations import operations_web_bp
from app.web.collector_kpi import collector_kpi_web_bp
from app.web.executive import executive_web_bp
from app.web.executive_v8 import executive_v8_bp
from app.web.incidents import incidents_web_bp
from app.web.tat_kpi import tat_kpi_web_bp
from app.web.dispatch_performance import dispatch_performance_web_bp
from app.api.patient_mobile.routes import patient_mobile_bp
from app.web.doctor_kpi import doctor_kpi_web_bp
from app.web.logistics import logistics_web_bp
from app.web.collector_mobile import collector_mobile_web_bp
from app.web.sample_public import sample_public_web_bp
from app.web.crm import crm_web_bp
from app.api.collector.routes import collector_bp
from app.web.collector_console import collector_console_web_bp
from app.web.audit_center import audit_center_web_bp
from app.api.ai_v2.batch import ai_batch_bp
from app.api.crm.routes import crm_bp
from app.api.lab.routes import lab_bp
from app.api.logistics.routes import logistics_platform_bp
from app.api.federation.routes import federation_bp
from app.web.federation import federation_web_bp
from app.web.ai_cds import ai_cds_web_bp
from app.api.knowledge.routes import (
    biomarkers_bp,
    correlations_bp,
    diseases_bp,
    guidelines_bp,
    knowledge_bp,
)
from app.web.knowledge_engine import knowledge_web_bp
def create_app():

    app = Flask(__name__)
    app.config.from_object(Config)
    app.secret_key = app.config["SECRET_KEY"]
    validate_config(app)
    init_observability(app)
    init_security(app)

    from app.core.db_pool import build_engine_options

    app.config.setdefault(
        "SQLALCHEMY_ENGINE_OPTIONS",
        build_engine_options(
            app.config.get("SQLALCHEMY_DATABASE_URI"),
            pool_size=app.config.get("DB_POOL_SIZE", 5),
            max_overflow=app.config.get("DB_MAX_OVERFLOW", 10),
            pool_recycle=app.config.get("DB_POOL_RECYCLE", 280),
        ),
    )

    db.init_app(app)
    init_performance(app)
    jwt.init_app(app)
    init_jwt_security(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(patients_bp)
    app.register_blueprint(laboratories_bp)
    app.register_blueprint(test_catalogs_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(order_items_bp)
    app.register_blueprint(sample_collections_bp)
    app.register_blueprint(test_results_bp)
    app.register_blueprint(ai_cds_bp)
    app.register_blueprint(ai_v2_bp)
    app.register_blueprint(companies_bp)
    app.register_blueprint(marketplace_bp)
    app.register_blueprint(partners_bp)
    app.register_blueprint(scheduling_bp)
    app.register_blueprint(order_lifecycle_bp)
    app.register_blueprint(collector_operations_bp)
    app.register_blueprint(order_execution_bp)
    app.register_blueprint(billing_bp)
    app.register_blueprint(partner_portal_bp)
    app.register_blueprint(reporting_bp)
    app.register_blueprint(results_bp)
    app.register_blueprint(interpretation_bp)
    app.register_blueprint(reference_ranges_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(notification_templates_bp)
    app.register_blueprint(patient_portal_bp)
    app.register_blueprint(clinic_portal_bp)
    app.register_blueprint(doctor_portal_bp)
    app.register_blueprint(contracts_bp)
    app.register_blueprint(contract_prices_bp)
    app.register_blueprint(invoices_bp)
    app.register_blueprint(payments_bp)
    app.register_blueprint(integrations_bp)
    app.register_blueprint(iot_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(seeds_bp)
    app.register_blueprint(mobile_bp)
    app.register_blueprint(workflow_bp)
    app.register_blueprint(home_collections_bp)
    app.register_blueprint(sample_trackings_bp)
    app.register_blueprint(incidents_bp)

    app.register_blueprint(auth_web_bp)
    app.register_blueprint(dashboard_web_bp)
    app.register_blueprint(patients_web_bp)
    app.register_blueprint(companies_web_bp)
    app.register_blueprint(marketplace_web_bp)
    app.register_blueprint(partners_web_bp)
    app.register_blueprint(scheduling_web_bp)
    app.register_blueprint(order_lifecycle_web_bp)
    app.register_blueprint(collector_operations_web_bp)
    app.register_blueprint(order_execution_web_bp)
    app.register_blueprint(partner_portal_web_bp)
    app.register_blueprint(reporting_bi_web_bp)
    app.register_blueprint(contracts_web_bp)
    app.register_blueprint(orders_web_bp)
    app.register_blueprint(invoices_web_bp)
    app.register_blueprint(payments_web_bp)
    app.register_blueprint(order_items_web_bp)
    app.register_blueprint(result_gateway_web_bp)
    app.register_blueprint(interpretation_admin_web_bp)
    app.register_blueprint(notifications_admin_web_bp)
    app.register_blueprint(patient_portal_v2_web_bp)
    app.register_blueprint(clinic_portal_v2_web_bp)
    app.register_blueprint(doctor_portal_v2_web_bp)
    app.register_blueprint(billing_invoice_web_bp)
    app.register_blueprint(payment_gateway_web_bp)
    app.register_blueprint(integrations_web_bp)
    app.register_blueprint(iot_web_bp)
    app.register_blueprint(test_results_web_bp)
    app.register_blueprint(reports_web_bp)
    app.register_blueprint(report_pdf_web_bp)
    app.register_blueprint(patient_portal_web_bp)
    app.register_blueprint(doctor_portal_web_bp)
    app.register_blueprint(home_collections_web_bp)
    app.register_blueprint(collector_portal_web_bp)
    app.register_blueprint(sample_tracking_web_bp)
    app.register_blueprint(result_upload_web_bp)
    app.register_blueprint(transport_boxes_bp)
    app.register_blueprint(transport_boxes_web_bp)
    app.register_blueprint(drivers_web_bp)
    app.register_blueprint(dispatch_web_bp)
    app.register_blueprint(dispatch_optimizer_web_bp)
    app.register_blueprint(lab_worklist_bp)
    app.register_blueprint(result_verify_web_bp)
    app.register_blueprint(analytics_web_bp)
    app.register_blueprint(alerts_bp)
    app.register_blueprint(alerts_web_bp)
    app.register_blueprint(operations_web_bp) 
    app.register_blueprint(operations_timeline_web_bp)
    app.register_blueprint(collector_kpi_web_bp)
    app.register_blueprint(executive_web_bp)
    app.register_blueprint(executive_v8_bp)
    app.register_blueprint(incidents_web_bp)
    app.register_blueprint(tat_kpi_web_bp)
    app.register_blueprint(dispatch_performance_web_bp)
    app.register_blueprint(patient_mobile_bp)
    app.register_blueprint(doctor_kpi_web_bp)
    app.register_blueprint(logistics_web_bp)
    app.register_blueprint(collector_mobile_web_bp)
    app.register_blueprint(sample_public_web_bp)
    app.register_blueprint(crm_web_bp)
    app.register_blueprint(collector_bp)
    app.register_blueprint(collector_console_web_bp)
    def home():
        return redirect("/login")

    app.register_blueprint(finance_web_bp)
    app.register_blueprint(crm_v2_web_bp)
    app.register_blueprint(executive_v9_bp)
    app.register_blueprint(home_web_bp)
    app.register_blueprint(ops_bp)
    app.register_blueprint(security_web_bp)
    app.register_blueprint(security_api_bp)
    app.register_blueprint(ai_interpret_v2_bp)
    app.register_blueprint(audit_center_web_bp)
    app.register_blueprint(admin_security_bp)
    app.register_blueprint(ai_batch_bp)
    app.register_blueprint(system_bp)
    app.register_blueprint(crm_bp)
    app.register_blueprint(lab_bp)
    app.register_blueprint(logistics_platform_bp)
    app.register_blueprint(monitor_web_bp)
    app.register_blueprint(result_files_bp)
    app.register_blueprint(shipments_bp)
    app.register_blueprint(shipments_web_bp)
    app.register_blueprint(logistics_v2_bp)
    app.register_blueprint(logistics_v2_web_bp)
    app.register_blueprint(box_qr_bp)
    app.register_blueprint(box_qr_web_bp)
    app.register_blueprint(federation_bp)
    app.register_blueprint(federation_web_bp)
    app.register_blueprint(ai_cds_web_bp)
    app.register_blueprint(knowledge_bp)
    app.register_blueprint(guidelines_bp)
    app.register_blueprint(biomarkers_bp)
    app.register_blueprint(diseases_bp)
    app.register_blueprint(correlations_bp)
    app.register_blueprint(knowledge_web_bp)
    finalize_observability(app)
    init_deployment(app)
    return app
