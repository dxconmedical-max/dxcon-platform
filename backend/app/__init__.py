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
from flask_cors import CORS

from app.core.config import Config

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
from app.api.scheduling.routes import scheduling_bp
from app.api.contracts.routes import contracts_bp
from app.api.contract_prices.routes import contract_prices_bp
from app.api.invoices.routes import invoices_bp
from app.api.payments.routes import payments_bp
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
from app.web.scheduling import scheduling_web_bp
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
from app.api.ai.routes import ai_bp
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
from app.api.alerts.routes import alerts_bp
from app.web.alerts import alerts_web_bp
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
def create_app():

    app = Flask(__name__)
    CORS(app)
    app.secret_key = "dxcon-secret-key"
    app.config.from_object(Config)

    db.init_app(app)
    jwt.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(patients_bp)
    app.register_blueprint(laboratories_bp)
    app.register_blueprint(test_catalogs_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(order_items_bp)
    app.register_blueprint(sample_collections_bp)
    app.register_blueprint(test_results_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(ai_v2_bp)
    app.register_blueprint(companies_bp)
    app.register_blueprint(marketplace_bp)
    app.register_blueprint(scheduling_bp)
    app.register_blueprint(contracts_bp)
    app.register_blueprint(contract_prices_bp)
    app.register_blueprint(invoices_bp)
    app.register_blueprint(payments_bp)
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
    app.register_blueprint(scheduling_web_bp)
    app.register_blueprint(contracts_web_bp)
    app.register_blueprint(orders_web_bp)
    app.register_blueprint(invoices_web_bp)
    app.register_blueprint(payments_web_bp)
    app.register_blueprint(order_items_web_bp)
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
    app.register_blueprint(monitor_web_bp)
    app.register_blueprint(result_files_bp)
    app.register_blueprint(shipments_bp)
    app.register_blueprint(shipments_web_bp)
    app.register_blueprint(logistics_v2_bp)
    app.register_blueprint(logistics_v2_web_bp)
    app.register_blueprint(box_qr_bp)
    app.register_blueprint(box_qr_web_bp)
    return app
