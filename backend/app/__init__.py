import os

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


def _apply_runtime_env_overrides(app: Flask) -> None:
    """Re-apply process env after Config class import.

    Test modules set DATABASE_URL (and related keys) before importing the app.
    Config attributes are evaluated once at import time, so later modules would
    otherwise inherit a stale URI (e.g. sqlite:///:memory:) and share the wrong DB.
    """
    database_url = os.getenv("DATABASE_URL")
    if database_url is not None and str(database_url).strip() != "":
        app.config["SQLALCHEMY_DATABASE_URI"] = database_url

    secret_key = os.getenv("SECRET_KEY")
    if secret_key is not None and str(secret_key).strip() != "":
        app.config["SECRET_KEY"] = secret_key

    jwt_secret = os.getenv("JWT_SECRET_KEY")
    if jwt_secret is not None and str(jwt_secret).strip() != "":
        app.config["JWT_SECRET_KEY"] = jwt_secret

    app_env = os.getenv("APP_ENV")
    if app_env is not None and str(app_env).strip() != "":
        app.config["APP_ENV"] = app_env


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    _apply_runtime_env_overrides(app)
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
