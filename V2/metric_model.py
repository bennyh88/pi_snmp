from dataclasses import dataclass, field
from datetime import datetime, timezone
from logging import Logger
from pathlib import Path
from metric import Metric
import json
from time import time


class MetricModel:

    def __init__(self, logger: Logger, config: dict):
        self.logger: Logger = logger
        self.metrics_list: dict[str, Metric] = {}
        # Builtin metrics
        self.collector_start_time: int = int(time())
        self.collector_status: dict = {}

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


    def _update_collector_status(self, plugin_name: str, status: int) -> None:
        self.collector_status[plugin_name] = status


    def _load_builtin_metrics(self) -> dict | None:
        self.logger.debug(f"Collector Status: {self.collector_status}")
        return {
            "collector_status": sum(self.collector_status.values()),
            "collector_age": int(time()) - self.collector_start_time
        }


    # loads the plugin_source file into a dict
    def _load_metrics(self, plugin_source: str) -> dict | None: 
        try:
            with open(plugin_source, "r") as f:
                return json.load(f)

        except FileNotFoundError:
            self.logger.error(f"Plugin Source file not found: {plugin_source}")

        except PermissionError:
            self.logger.error(f"Permission denied reading: {plugin_source}")

        except json.JSONDecodeError as err:
            self.logger.error(
                f"Invalid JSON in {plugin_source}: "
                f"line {err.lineno}, column {err.colno}: {err.msg}"
            )

        except OSError as err:
            self.logger.error(f"Failed to read {plugin_source}: {err}")

        except Exception:
            self.logger.exception(f"Unexpected error loading {plugin_source}")

        return None


    def _update_plugin_metrics(self, m: Metric) -> None:

        if m.plugin_source == "builtin":
            self._update_builtin_metric(m)
            return
        
        # If the file has not changed, then no need to reload
        datafile = Path(m.plugin_source)
        datafile_timestamp = datafile.stat().st_mtime

        if datafile_timestamp == m.timestamp:
            self.logger.debug(f"plugin_source for {m.plugin_name} has not updated, don't reload")
            return
        self.logger.debug(f"plugin_source for {m.plugin_name} updated, reload data")

        data: dict = self._load_metrics(m.plugin_source)
        
        if data is None:
            self.logger.warning(f"Failed to load data from {m.plugin_source}")
            self._update_collector_status(m.plugin_name, 1)
            return None

        # Update all metrics associated with the plugin
        for metric in self.metrics_list.values():
 
            if metric.plugin_name == m.plugin_name:

                # make sure data exists for the metric
                if metric.name not in data:
                    self.logger.warning(f"Failed to find key for {metric.pathname} in plugin_source")
                    self._update_collector_status(metric.plugin_name, 1)
                    return None

                metric.value = data.get(metric.name)
                metric.timestamp = datafile_timestamp

        # reached here, so set status to success for the plugin
        self._update_collector_status(m.plugin_name, 0)


    def _update_builtin_metric(self, metric: Metric) -> Metric | None:

        data = self._load_builtin_metrics()

        if data is None:
            self.logger.warning(f"Failed to load data {metric.oid}")
            self._update_collector_status(metric.plugin_name, 1)
            return None

        if metric.name not in data:
            self.logger.warning(f"Failed to find key for {metric.pathname} in plugin_source")
            self._update_collector_status(metric.plugin_name, 1)
            return None
        
        metric.value = data.get(metric.name)

        self._update_collector_status(metric.plugin_name, 0)

        return metric


    def get_metric(self, oid: str) -> Metric | None:

        metric: Metric = self.metrics_list.get(oid)

        if metric is None:
            self.logger.warning(f"Metric not found for {oid}")
            return None

        # Make sure we are up to date
        self._update_plugin_metrics(metric)
        
        return metric


    def get_next_metric(self, current_oid: str) -> Metric | None:
        sorted_oids = sorted(self.metrics_list.keys())

        for oid in sorted_oids:
            if oid > current_oid:
                return self.get_metric(oid)
        
        return None


    def to_string(self) -> str:     
        return json.dumps(
            [[metric.to_dict() for metric in self.metrics_list.values()]],
            indent=4
        )