from app.core.api_response import init_api_response_envelope
from app.core.logging_config import configure_logging
from app.core.request_context import init_request_context
from app.core.tenancy.middleware import init_tenant_middleware


def register_middleware(app):
    configure_logging(app)
    init_request_context(app)
    init_tenant_middleware(app)
    init_api_response_envelope(app)
