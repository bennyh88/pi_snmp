from dataclasses import dataclass, field
from datetime import datetime, timezone

from metric import Metric


@dataclass(slots=True)
class MetricSet:
    plugin_name: str
    metrics: list[Metric]

    collected_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self) -> dict:
        return {
            "plugin_name": self.plugin_name,
            "collected_at": self.collected_at.isoformat(),
            "metrics": [
                metric.to_dict()
                for metric in self.metrics
            ]
        }