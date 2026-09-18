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
    """
    Represents a single metric collected by a plugin.
    """

    name: str
    value: Any
    metric_type: MetricType

    description: str = ""
    unit: str = ""
    source: str = ""

    oid: str | None = None
    snmp_type: str | None = None

    labels: dict[str, str] = field(default_factory=dict)

    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self) -> dict:
        data = asdict(self)
        data["metric_type"] = self.metric_type.value
        data["timestamp"] = self.timestamp.isoformat()
        return data