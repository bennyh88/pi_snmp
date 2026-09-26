import psutil

from agent.metric import Metric, MetricType
from agent.metric_set import MetricSet
from agent.plugin_base import PluginBase


class CpuPlugin(PluginBase):

    @property
    def name(self) -> str:
        return "cpu"

    def collect(self) -> MetricSet:

        cpu_percent = psutil.cpu_percent()

        metrics = [
            Metric(
                name="cpu_usage_percent",
                value=cpu_percent,
                metric_type=MetricType.GAUGE,
                description="Current CPU utilisation",
                unit="percent",
                source="psutil",
                oid=".1.3.6.1.4.1.99999.1.1",
                snmp_type="Gauge32"
            )
        ]

        return MetricSet(
            plugin_name=self.name,
            metrics=metrics
        )