from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class HL7Message:
    message_type: str
    segments: Dict[str, dict] = field(default_factory=dict)
    raw: str = ""

    def to_dict(self):
        return {
            "message_type": self.message_type,
            "segments": self.segments,
            "raw": self.raw,
        }
