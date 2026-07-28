from flask import Flask

from app.core.config import Config
from app.core.config_validation import validate_config
from app.core.deployment import init_deployment
from app.core.observability import finalize_observability
from app.bootstrap.blueprints import register_blueprints
from app.bootstrap.errors import register_errors
from app.bootstrap.extensions import init_extensions
from app.bootstrap.middleware import register_middleware
from app.models import *


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.secret_key = app.config["SECRET_KEY"]
    validate_config(app)

    init_extensions(app)
    register_middleware(app)
    register_blueprints(app)
    register_errors(app)

    finalize_observability(app)
    # Gunicorn loads `run:app` at import time — DB/startup checks need an
    # application context or SQLAlchemy raises "Working outside of application context".
    with app.app_context():
        init_deployment(app)
    return app
