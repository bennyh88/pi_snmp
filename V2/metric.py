from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class MetricType(str, Enum):
    GAUGE = "gauge"
    COUNTER = "counter"
    STATE = "state"
    STRING = "string"


@dataclass(slots=True)
class Metric:
    name: str
    pathname: str
    oid: str
    datatype: str # MetricType
    plugin_name: str
    plugin_source: str
    value: Any | None = None

    # timestamp: datetime = field(
    #     default_factory=lambda: datetime.now(timezone.utc)
    # )

    def to_dict(self) -> dict:
        data = asdict(self)
        # data["timestamp"] = self.timestamp.isoformat()
        return data