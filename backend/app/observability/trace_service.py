from flask import g, request

from app.observability.trace_context import TraceContext, get_current_trace_context, set_current_trace_context


class TraceService:
    @staticmethod
    def start_trace(trace_id=None):
        incoming = request.headers.get("X-Trace-ID") if request else None
        parent_span = request.headers.get("X-Span-ID") if request else None
        context = TraceContext.root(trace_id=trace_id or incoming)
        if parent_span:
            context.parent_span_id = parent_span
        set_current_trace_context(context)
        if g:
            g.trace_id = context.trace_id
            g.span_id = context.span_id
            g.parent_span_id = context.parent_span_id
        return context.to_dict()

    @staticmethod
    def start_span(name):
        current = get_current_trace_context() or TraceContext.root()
        span = current.child()
        set_current_trace_context(span)
        return {"span": span.to_dict(), "name": name}

    @staticmethod
    def current_context():
        current = get_current_trace_context()
        if current:
            return current.to_dict()
        if g and getattr(g, "trace_id", None):
            return {
                "trace_id": g.trace_id,
                "span_id": getattr(g, "span_id", None),
                "parent_span_id": getattr(g, "parent_span_id", None),
            }
        return TraceService.start_trace()

    @staticmethod
    def inject_headers(headers=None):
        headers = dict(headers or {})
        context = get_current_trace_context()
        if context:
            headers.update(context.headers())
        return headers

    @staticmethod
    def init_app(app):
        @app.before_request
        def _start_trace_context():
            TraceService.start_trace()
