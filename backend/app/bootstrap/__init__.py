"""Application bootstrap helpers for factory wiring."""

from app.bootstrap.blueprints import register_blueprints
from app.bootstrap.errors import register_errors
from app.bootstrap.extensions import init_extensions
from app.bootstrap.middleware import register_middleware

__all__ = [
    "init_extensions",
    "register_blueprints",
    "register_errors",
    "register_middleware",
]
