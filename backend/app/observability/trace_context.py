import uuid
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TraceContext:
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None

    @classmethod
    def root(cls, trace_id=None):
        trace = trace_id or str(uuid.uuid4())
        return cls(trace_id=trace, span_id=str(uuid.uuid4())[:16])

    def child(self):
        return TraceContext(
            trace_id=self.trace_id,
            span_id=str(uuid.uuid4())[:16],
            parent_span_id=self.span_id,
        )

    def to_dict(self):
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
        }

    def headers(self):
        return {
            "X-Trace-ID": self.trace_id,
            "X-Span-ID": self.span_id,
            "X-Parent-Span-ID": self.parent_span_id or "",
        }


_current_context: TraceContext = None


def get_current_trace_context():
    return _current_context


def set_current_trace_context(context: TraceContext):
    global _current_context
    _current_context = context
    return context
