from app.core.jwt_auth import init_jwt_security
from app.core.performance import init_performance
from app.core.security import init_security
from app.extensions.db import db
from app.extensions.jwt import jwt
from app.observability.platform_init import init_observability_platform
from app.operations.maintenance_service import MaintenanceService


def init_extensions(app):
    from app.ai_platform.factory import init_ai_platform
    from app.core.db_pool import build_engine_options
    from app.storage.factory import init_storage_platform

    init_storage_platform(app)
    MaintenanceService.init_app(app)
    init_security(app)

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
    init_ai_platform(app)
    init_performance(app)
    jwt.init_app(app)
    init_jwt_security(app)
    init_observability_platform(app)
