from flask import Flask

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
from app.api.sample_collections.routes import sample_collections_bp
from app.api.test_results.routes import test_results_bp
from app.api.ai.routes import ai_bp
from app.api.companies.routes import companies_bp
from app.api.contracts.routes import contracts_bp
from app.api.contract_prices.routes import contract_prices_bp
from app.api.seeds.routes import seeds_bp
from app.api.order_items.routes import order_items_bp
from app.api.invoices.routes import invoices_bp
from app.api.payments.routes import payments_bp
def create_app():
   
    app = Flask(__name__)

    app.config.from_object(Config)

    db.init_app(app)
    jwt.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(patients_bp)
    app.register_blueprint(laboratories_bp)
    app.register_blueprint(test_catalogs_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(sample_collections_bp)
    app.register_blueprint(test_results_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(companies_bp)
    app.register_blueprint(contracts_bp)
    app.register_blueprint(contract_prices_bp)
    app.register_blueprint(seeds_bp)
    app.register_blueprint(order_items_bp)
    app.register_blueprint(invoices_bp)
    app.register_blueprint(payments_bp)
    @app.route("/")
    def home():
        return {
            "project": "DxCon",
            "status": "running",
            "phase": "TEST_RESULT_MODULE"
        }

    return app
