from app.api.test_catalogs.routes import test_catalogs_bp
from app.api.orders.routes import orders_bp
from app.api.ai.routes import ai_bp
from app.api.seeds.routes import seeds_b
from app.api.payments.routes import payments_bp
     app.register_blueprint(ai_bp)
     app.register_blueprint(seeds_bp)
     app.register_blueprint(payments_bp)
