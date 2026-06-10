from flask import Flask, redirect

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
from app.api.ai.routes import ai_bp
from app.api.companies.routes import companies_bp
from app.api.contracts.routes import contracts_bp
from app.api.contract_prices.routes import contract_prices_bp
from app.api.invoices.routes import invoices_bp
from app.api.payments.routes import payments_bp
from app.api.dashboard.routes import dashboard_bp
from app.api.seeds.routes import seeds_bp
from app.api.home_collections.routes import home_collections_bp
from app.api.sample_trackings.routes import sample_trackings_bp

from app.web.auth import auth_web_bp
from app.web.dashboard import dashboard_web_bp
from app.web.patients import patients_web_bp
from app.web.companies import companies_web_bp
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
def create_app():

    app = Flask(__name__)
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
    app.register_blueprint(companies_bp)
    app.register_blueprint(contracts_bp)
    app.register_blueprint(contract_prices_bp)
    app.register_blueprint(invoices_bp)
    app.register_blueprint(payments_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(seeds_bp)
    app.register_blueprint(home_collections_bp)
    app.register_blueprint(sample_trackings_bp)

    app.register_blueprint(auth_web_bp)
    app.register_blueprint(dashboard_web_bp)
    app.register_blueprint(patients_web_bp)
    app.register_blueprint(companies_web_bp)
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
    @app.route("/")
    def home():
        return redirect("/login")

    return app
