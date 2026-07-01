from app.observability.trace_service import TraceService


def init_observability_platform(app):
    TraceService.init_app(app)

    @app.after_request
    def _record_platform_metrics(response):
        if not app.config.get("OBSERVABILITY_PLATFORM_ENABLED", True):
            return response
        from flask import g
        import time

        duration_ms = 0.0
        if g and getattr(g, "request_start_time", None) is not None:
            duration_ms = round((time.perf_counter() - g.request_start_time) * 1000, 2)
        from app.observability.metrics_service import MetricsPlatformService

        try:
            MetricsPlatformService.record_http_request(duration_ms, response.status_code)
        except Exception:
            pass
        return response
