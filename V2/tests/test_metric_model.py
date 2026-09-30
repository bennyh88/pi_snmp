import json
import logging
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
from time import time

from metric import Metric
from metric_model import MetricModel


class TestMetricModel(unittest.TestCase):

    def setUp(self):
        """
        Runs before every test.

        MetricModel currently stores metrics_list, collector_status and
        collector_start_time as class attributes. Reset them here so that
        tests do not affect each other.
        """

        self.logger = MagicMock(spec=logging.Logger)

        self.config = {
            "base_oid": ".1.3.6.1.4.1.99999",
            "plugins": {
                "test_plugin": {
                    "plugin_oid": 1,
                    "plugin_source": "test_plugin.json",
                    "metrics": {
                        "status": {
                            "oid": 1,
                            "datatype": "integer"
                        },
                        "request_count": {
                            "oid": 2,
                            "datatype": "integer"
                        }
                    }
                }
            }
        }

        self.model = MetricModel(
            logger=self.logger,
            config=self.config
        )

    def test_initialisation_creates_metrics(self):
        self.assertEqual(len(self.model.metrics_list), 2)

        self.assertIn(
            ".1.3.6.1.4.1.99999.1.1",
            self.model.metrics_list
        )

        self.assertIn(
            ".1.3.6.1.4.1.99999.1.2",
            self.model.metrics_list
        )

    def test_initialisation_creates_metric_with_correct_values(self):
        oid = ".1.3.6.1.4.1.99999.1.1"

        metric = self.model.metrics_list[oid]

        self.assertEqual(metric.name, "status")
        self.assertEqual(metric.pathname, "test_plugin.status")
        self.assertEqual(metric.oid, oid)
        self.assertEqual(metric.datatype, "integer")
        self.assertEqual(metric.plugin_name, "test_plugin")
        self.assertEqual(metric.plugin_source, "test_plugin.json")
        self.assertIsNone(metric.value)

    def test_initialisation_sets_collector_status(self):
        self.assertEqual(
            self.model.collector_status["test_plugin"],
            0
        )

    def test_get_unknown_metric_returns_none(self):
        result = self.model.get_metric(
            ".1.3.6.1.4.1.99999.999.1"
        )

        self.assertIsNone(result)

        self.logger.warning.assert_called_once_with(
            "Metric not found for .1.3.6.1.4.1.99999.999.1"
        )

    def test_load_metrics_reads_valid_json(self):
        test_data = {
            "status": 1,
            "request_count": 25
        }

        with tempfile.TemporaryDirectory() as temp_directory:
            json_file = Path(temp_directory) / "metrics.json"

            json_file.write_text(
                json.dumps(test_data),
                encoding="utf-8"
            )

            result = self.model._load_metrics(
                str(json_file)
            )

        self.assertEqual(result, test_data)

    def test_load_metrics_returns_none_when_file_missing(self):
        filename = "file_that_does_not_exist.json"

        result = self.model._load_metrics(filename)

        self.assertIsNone(result)

        self.logger.error.assert_called_once_with(
            f"Plugin Source file not found: {filename}"
        )

    def test_load_metrics_returns_none_for_invalid_json(self):
        with tempfile.TemporaryDirectory() as temp_directory:
            json_file = Path(temp_directory) / "invalid.json"

            json_file.write_text(
                '{"status": invalid}',
                encoding="utf-8"
            )

            result = self.model._load_metrics(
                str(json_file)
            )

        self.assertIsNone(result)
        self.logger.error.assert_called_once()

        logged_message = self.logger.error.call_args.args[0]

        self.assertIn("Invalid JSON", logged_message)

    def test_get_metric_loads_plugin_data(self):
        test_data = {
            "status": 1,
            "request_count": 25
        }

        with tempfile.TemporaryDirectory() as temp_directory:
            json_file = Path(temp_directory) / "metrics.json"

            json_file.write_text(
                json.dumps(test_data),
                encoding="utf-8"
            )

            for metric in self.model.metrics_list.values():
                metric.plugin_source = str(json_file)
                metric.timestamp = 0

            result = self.model.get_metric(
                ".1.3.6.1.4.1.99999.1.1"
            )

            request_count_metric = self.model.metrics_list[
                ".1.3.6.1.4.1.99999.1.2"
            ]

        self.assertEqual(result.value, 1)
        self.assertEqual(request_count_metric.value, 25)

        self.assertEqual(
            self.model.collector_status["test_plugin"],
            0
        )

    def test_plugin_data_is_not_reloaded_when_file_has_not_changed(self):
        metric = self.model.metrics_list[
            ".1.3.6.1.4.1.99999.1.1"
        ]

        with tempfile.TemporaryDirectory() as temp_directory:
            json_file = Path(temp_directory) / "metrics.json"

            json_file.write_text(
                json.dumps({"status": 1}),
                encoding="utf-8"
            )

            metric.plugin_source = str(json_file)
            metric.timestamp = json_file.stat().st_mtime

            with patch.object(
                self.model,
                "_load_metrics"
            ) as mock_load_metrics:

                result = self.model.get_metric(metric.oid)

        self.assertIs(result, metric)
        mock_load_metrics.assert_not_called()
        self.logger.debug.assert_called()

    def test_failed_plugin_load_sets_collector_status(self):
        metric = self.model.metrics_list[
            ".1.3.6.1.4.1.99999.1.1"
        ]

        with tempfile.TemporaryDirectory() as temp_directory:
            json_file = Path(temp_directory) / "metrics.json"

            json_file.write_text("{}", encoding="utf-8")

            metric.plugin_source = str(json_file)
            metric.timestamp = 0

            with patch.object(
                self.model,
                "_load_metrics",
                return_value=None
            ):
                result = self.model.get_metric(metric.oid)

        self.assertIs(result, metric)

        self.assertEqual(
            self.model.collector_status["test_plugin"],
            1
        )

        self.logger.warning.assert_called_with(
            f"Failed to load data from {json_file}"
        )

    def test_update_builtin_metric(self):
        builtin_metric = Metric(
            name="collector_status",
            pathname="builtin.collector_status",
            oid=".1.3.6.1.4.1.99999.0.1",
            datatype="integer",
            plugin_name="builtin",
            plugin_source="builtin",
            value=None
        )

        self.model.collector_status["builtin"] = 0
        self.model.collector_status["test_plugin"] = 1

        with patch.object(
            self.model,
            "_load_builtin_metrics",
            return_value={
                "collector_status": 1,
                "collector_age": 50
            }
        ):
            result = self.model._update_builtin_metric(
                builtin_metric
            )

        self.assertIs(result, builtin_metric)
        self.assertEqual(result.value, 1)
        self.assertEqual(self.model.collector_status["builtin"], 0)

    def test_update_builtin_metric_returns_none_when_key_missing(self):
        builtin_metric = Metric(
            name="unknown_builtin_metric",
            pathname="builtin.unknown_builtin_metric",
            oid=".1.3.6.1.4.1.99999.0.99",
            datatype="integer",
            plugin_name="builtin",
            plugin_source="builtin",
            value=None
        )

        self.model.collector_status["builtin"] = 0

        with patch.object(
            self.model,
            "_load_builtin_metrics",
            return_value={
                "collector_status": 0,
                "collector_age": 50
            }
        ):
            result = self.model._update_builtin_metric(
                builtin_metric
            )

        self.assertIsNone(result)
        self.assertEqual(self.model.collector_status["builtin"], 1)
        self.logger.warning.assert_called_once()

    def test_load_builtin_metrics_returns_status_and_age(self):
        self.model.collector_start_time = 1_000

        self.model.collector_status = {
            "test_plugin": 0,
            "operator_count": 1
        }

        with patch("metric_model.time", return_value=1_100):
            result = self.model._load_builtin_metrics()

        self.assertEqual(
            result,
            {
                "collector_status": 1,
                "collector_age": 100
            }
        )

    def test_get_next_metric_returns_next_oid(self):
        current_oid = ".1.3.6.1.4.1.99999.1.1"

        expected_metric = self.model.metrics_list[
            ".1.3.6.1.4.1.99999.1.2"
        ]

        with patch.object(
            self.model,
            "get_metric",
            return_value=expected_metric
        ) as mock_get_metric:

            result = self.model.get_next_metric(current_oid)

        self.assertIs(result, expected_metric)

        mock_get_metric.assert_called_once_with(
            ".1.3.6.1.4.1.99999.1.2"
        )

    def test_get_next_metric_returns_none_after_final_oid(self):
        result = self.model.get_next_metric(
            ".1.3.6.1.4.1.99999.999.999"
        )

        self.assertIsNone(result)



if __name__ == "__main__":
    unittest.main()
