from dataclasses import dataclass, field
from datetime import datetime, timezone
from logging import Logger

from metric import Metric
import json
from time import time


class MetricModel:
    metrics_list: dict[str, Metric | None] = {}
    logger: Logger

    # Builtin metrics
    collector_start_time: int = int(time())
    collector_status: dict = {}


    def __init__(self, logger: Logger, config: dict):
        self.logger: Logger = logger

        base_oid: str = config["base_oid"]
        plugins: dict = config["plugins"]

        for plugin_name, plugin_config in plugins.items():

            # Add each plugin to the collector_status
            self.collector_status[plugin_name] = 0

            plugin_oid: int = plugin_config["plugin_oid"]
            plugin_source: str = plugin_config["plugin_source"]
            metrics: dict = plugin_config['metrics']

            for metric_name, metric_config in metrics.items():

                oid: str = f"{base_oid}.{plugin_oid}.{metric_config['oid']}"

                self.metrics_list[oid] = (
                    Metric(
                        name=metric_name,
                        pathname=f"{plugin_name}.{metric_name}",
                        oid=oid,
                        datatype=metric_config['datatype'],
                        plugin_name=plugin_name,
                        plugin_source=plugin_source,
                        value=None
                    )
                )


    def __update_collector_status(self, plugin_name: str, status: int) -> None:
        self.collector_status[plugin_name] = status


    def __load_builtin_metrics(self) -> dict | None:
        return {
            "collector_status": sum(self.collector_status.values()),
            "collector_age": int(time()) - self.collector_start_time
        }


    # loads the plugin_source file into a dict
    def __load_metrics(self, metric: Metric) -> dict | None: 
        try:
            with open(metric.plugin_source, "r") as f:
                return json.load(f)

        except FileNotFoundError:
            self.logger.error(f"Plugin Source file not found: {metric.plugin_source}")

        except PermissionError:
            self.logger.error(f"Permission denied reading: {metric.plugin_source}")

        except json.JSONDecodeError as err:
            self.logger.error(
                f"Invalid JSON in {metric.plugin_source}: "
                f"line {err.lineno}, column {err.colno}: {err.msg}"
            )

        except OSError as err:
            self.logger.error(f"Failed to read {metric.plugin_source}: {err}")

        except Exception:
            self.logger.exception(f"Unexpected error loading {metric.plugin_source}")

        return None


    def update_metric(self, metric: Metric) -> Metric:

        if metric.plugin_source == "builtin":
            data = self.__load_builtin_metrics()
        else:
            data = self.__load_metrics(metric)

        if data is None:
            self.logger.warning(f"Failed to load data {metric.oid}")
            self.__update_collector_status(metric.plugin_name, 1)
            return None

        # update the metric with the value
        if data.get(metric.name) is None:
            self.logger.warning(f"Failed to find key for {metric.pathname} in plugin_source")
            self.__update_collector_status(metric.plugin_name, 1)
            return None
        
        metric.value = data.get(metric.name)

        self.__update_collector_status(metric.plugin_name, 0)

        return metric


    def get_metric(self, oid: str) -> Metric:
        metric: Metric = self.metrics_list.get(oid)
        if metric is None:
            self.logger.warning(f"Metric not found for {oid}")
            self.__update_collector_status(metric.plugin_name, 1)
            return None

        metric = self.update_metric(metric)

        return metric


    def get_next_metric(self, current_oid: str) -> Metric:
        sorted_oids = sorted(self.metrics_list.keys())

        for oid in sorted_oids:
            if oid > current_oid:
                return self.get_metric(oid)
        
        return None


    def to_string(self):     
        return json.dumps(
            [[metric.to_dict() for metric in self.metrics_list.values()]],
            indent=4
        )