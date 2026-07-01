from app.core.api_response import init_api_response_envelope
from app.core.errors import register_error_handlers
from app.core.logging_config import configure_logging
from app.core.metrics import metrics
from app.core.request_context import init_request_context


def init_observability(app):
    configure_logging(app)
    init_request_context(app)
    register_error_handlers(app)
    init_api_response_envelope(app)


def finalize_observability(app):
    metrics.set_route_count(len(list(app.url_map.iter_rules())))
