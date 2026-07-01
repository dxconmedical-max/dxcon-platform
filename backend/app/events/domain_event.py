from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional
import uuid


@dataclass
class DomainEvent:
    event_type: str
    payload: Dict[str, Any] = field(default_factory=dict)
    source: str = "dxcon"
    correlation_id: Optional[str] = None
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "payload": self.payload,
            "source": self.source,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp,
        }
