from dataclasses import dataclass, field
from datetime import datetime, timezone

from metric import Metric



class MetricModel:
    metrics_list: list[Metric | None] = []

    def __init__(self, config: dict):
        base_oid: str = config["base_oid"]

        # Load the builtins
        plugin_oid: int = config["builtin"]["plugin_oid"]

        plugins = config["plugins"]
        for plugin_name, plugin_config in plugins.items():
            plugin_oid: int = config["plugins"][plugin_name]["plugin_oid"]

            # print(plugin_oid)
            # print(plugin_name)
            # print(f"Plugin: {plugin_name}")
            # print(f"Plugin OID: {plugin_config['plugin_oid']}")

            metrics = plugin_config['metrics']
            for metric_name, metric_config in metrics.items():
                # print(f"\tMetric Name: {metric_name}")
                # print(f"\t\tMetric OID: {metric_config['oid']}")
                # print(f"\t\tMetric Datatype: {metric_config['datatype']}")

                self.metrics_list.append(
                    Metric(
                        name=metric_name,
                        pathname=f"{plugin_name}.{metric_name}",
                        oid=f"{base_oid}.{plugin_oid}.{metric_config['oid']}",
                        datatype=metric_config['datatype'],
                        source_plugin=plugin_name,
                        value=None
                    )
                )


        # For testing
        for metric in self.metrics_list:
            print(metric.to_dict())

    #def export_metrics
            