from app.core.statuses import VALID_DOMAIN_EVENTS


class EventRegistry:
    _handlers = {}

    @classmethod
    def register_handler(cls, event_type: str, handler):
        cls._handlers.setdefault(event_type, []).append(handler)

    @classmethod
    def list_event_types(cls):
        return list(VALID_DOMAIN_EVENTS)

    @classmethod
    def handlers_for(cls, event_type: str):
        return cls._handlers.get(event_type, [])

    @classmethod
    def reset(cls):
        cls._handlers.clear()
