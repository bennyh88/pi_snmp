import io
import logging
import unittest
from unittest.mock import MagicMock, mock_open, patch

import yaml

import collector


class TestReadConfig(unittest.TestCase):

    def setUp(self):
        collector.logger = MagicMock(spec=logging.Logger)

    def test_read_config_returns_config_section(self):
        yaml_data = {
            "config": {
                "base_oid": ".1.3.6.1.4.1.99999",
                "plugins": {}
            }
        }

        with patch("builtins.open", mock_open()):
            with patch(
                "collector.yaml.safe_load",
                return_value=yaml_data
            ):
                result = collector.read_config()

        self.assertEqual(
            result,
            {
                "base_oid": ".1.3.6.1.4.1.99999",
                "plugins": {}
            }
        )

    def test_read_config_opens_config_file(self):
        yaml_data = {
            "config": {
                "base_oid": ".1.3.6.1.4.1.99999",
                "plugins": {}
            }
        }

        mocked_open = mock_open()

        with patch("builtins.open", mocked_open):
            with patch(
                "collector.yaml.safe_load",
                return_value=yaml_data
            ):
                collector.read_config()

        mocked_open.assert_called_once_with(
            collector.CONFIG_FILE,
            "r"
        )

    def test_read_config_exits_when_file_not_found(self):
        with patch(
            "builtins.open",
            side_effect=FileNotFoundError
        ):
            with self.assertRaises(SystemExit) as context:
                collector.read_config()

        self.assertEqual(context.exception.code, 1)

        collector.logger.critical.assert_called_once_with(
            f"Configuration file not found: {collector.CONFIG_FILE}"
        )

    def test_read_config_exits_for_invalid_yaml(self):
        yaml_error = yaml.YAMLError("Invalid YAML")

        with patch("builtins.open", mock_open()):
            with patch(
                "collector.yaml.safe_load",
                side_effect=yaml_error
            ):
                with self.assertRaises(SystemExit) as context:
                    collector.read_config()

        self.assertEqual(context.exception.code, 1)

        collector.logger.critical.assert_called_once()

        logged_message = collector.logger.critical.call_args.args[0]

        self.assertIn("Invalid YAML", logged_message)

    def test_read_config_exits_when_config_section_missing(self):
        yaml_data = {
            "something_else": {}
        }

        with patch("builtins.open", mock_open()):
            with patch(
                "collector.yaml.safe_load",
                return_value=yaml_data
            ):
                with self.assertRaises(SystemExit) as context:
                    collector.read_config()

        self.assertEqual(context.exception.code, 1)

        collector.logger.critical.assert_called_once_with(
            f"Missing 'config' section in {collector.CONFIG_FILE}"
        )

    def test_read_config_logs_unexpected_exception(self):
        with patch(
            "builtins.open",
            side_effect=RuntimeError("Unexpected problem")
        ):
            with self.assertRaises(SystemExit) as context:
                collector.read_config()

        self.assertEqual(context.exception.code, 1)

        collector.logger.exception.assert_called_once_with(
            f"Unexpected error loading {collector.CONFIG_FILE}"
        )


class TestMain(unittest.TestCase):

    def setUp(self):
        collector.logger = MagicMock(spec=logging.Logger)

        self.config = {
            "base_oid": ".1.3.6.1.4.1.99999",
            "plugins": {}
        }

    def test_main_constructs_metric_model(self):
        mock_model = MagicMock()
        mock_model.to_string.return_value = "[]"

        with patch(
            "collector.read_config",
            return_value=self.config
        ):
            with patch(
                "collector.MetricModel",
                return_value=mock_model
            ) as mock_metric_model:
                with patch(
                    "collector.sys.stdin.readline",
                    side_effect=KeyboardInterrupt
                ):
                    with self.assertRaises(KeyboardInterrupt):
                        collector.main()

        mock_metric_model.assert_called_once_with(
            collector.logger,
            self.config
        )

        collector.logger.info.assert_called_with("READY")

    def test_main_responds_to_ping(self):
        mock_model = MagicMock()
        mock_model.to_string.return_value = "[]"

        fake_stdout = io.StringIO()

        with patch(
            "collector.read_config",
            return_value=self.config
        ):
            with patch(
                "collector.MetricModel",
                return_value=mock_model
            ):
                with patch(
                    "collector.sys.stdin.readline",
                    side_effect=[
                        "PING\n",
                        KeyboardInterrupt
                    ]
                ):
                    with patch(
                        "collector.sys.stdout",
                        fake_stdout
                    ):
                        with self.assertRaises(KeyboardInterrupt):
                            collector.main()

        self.assertEqual(
            fake_stdout.getvalue().strip(),
            "PONG"
        )

        collector.logger.debug.assert_any_call(
            "input: PING"
        )

        collector.logger.debug.assert_any_call(
            "output: PONG"
        )

    def test_main_get_returns_metric(self):
        test_oid = ".1.3.6.1.4.1.99999.1.1"

        mock_metric = MagicMock()
        mock_metric.oid = test_oid
        mock_metric.datatype = "integer"
        mock_metric.value = 25

        mock_model = MagicMock()
        mock_model.to_string.return_value = "[]"
        mock_model.get_metric.return_value = mock_metric

        fake_stdout = io.StringIO()

        with patch(
            "collector.read_config",
            return_value=self.config
        ):
            with patch(
                "collector.MetricModel",
                return_value=mock_model
            ):
                with patch(
                    "collector.sys.stdin.readline",
                    side_effect=[
                        "get\n",
                        f"{test_oid}\n",
                        KeyboardInterrupt
                    ]
                ):
                    with patch(
                        "collector.sys.stdout",
                        fake_stdout
                    ):
                        with self.assertRaises(KeyboardInterrupt):
                            collector.main()

        output_lines = fake_stdout.getvalue().splitlines()

        self.assertEqual(
            output_lines,
            [
                test_oid,
                "integer",
                "25"
            ]
        )

        mock_model.get_metric.assert_called_once_with(
            test_oid
        )

    def test_main_get_returns_none_when_metric_not_found(self):
        test_oid = ".1.3.6.1.4.1.99999.999.1"

        mock_model = MagicMock()
        mock_model.to_string.return_value = "[]"
        mock_model.get_metric.return_value = None

        fake_stdout = io.StringIO()

        with patch(
            "collector.read_config",
            return_value=self.config
        ):
            with patch(
                "collector.MetricModel",
                return_value=mock_model
            ):
                with patch(
                    "collector.sys.stdin.readline",
                    side_effect=[
                        "get\n",
                        f"{test_oid}\n",
                        KeyboardInterrupt
                    ]
                ):
                    with patch(
                        "collector.sys.stdout",
                        fake_stdout
                    ):
                        with self.assertRaises(KeyboardInterrupt):
                            collector.main()

        self.assertEqual(
            fake_stdout.getvalue().strip(),
            "NONE"
        )

        mock_model.get_metric.assert_called_once_with(
            test_oid
        )

    def test_main_getnext_returns_next_metric(self):
        current_oid = ".1.3.6.1.4.1.99999.1.1"
        next_oid = ".1.3.6.1.4.1.99999.1.2"

        mock_metric = MagicMock()
        mock_metric.oid = next_oid
        mock_metric.datatype = "integer"
        mock_metric.value = 50

        mock_model = MagicMock()
        mock_model.to_string.return_value = "[]"
        mock_model.get_next_metric.return_value = mock_metric

        fake_stdout = io.StringIO()

        with patch(
            "collector.read_config",
            return_value=self.config
        ):
            with patch(
                "collector.MetricModel",
                return_value=mock_model
            ):
                with patch(
                    "collector.sys.stdin.readline",
                    side_effect=[
                        "getnext\n",
                        f"{current_oid}\n",
                        KeyboardInterrupt
                    ]
                ):
                    with patch(
                        "collector.sys.stdout",
                        fake_stdout
                    ):
                        with self.assertRaises(KeyboardInterrupt):
                            collector.main()

        self.assertEqual(
            fake_stdout.getvalue().splitlines(),
            [
                next_oid,
                "integer",
                "50"
            ]
        )

        mock_model.get_next_metric.assert_called_once_with(
            current_oid
        )

    def test_main_getnext_returns_none_at_end(self):
        current_oid = ".1.3.6.1.4.1.99999.999.999"

        mock_model = MagicMock()
        mock_model.to_string.return_value = "[]"
        mock_model.get_next_metric.return_value = None

        fake_stdout = io.StringIO()

        with patch(
            "collector.read_config",
            return_value=self.config
        ):
            with patch(
                "collector.MetricModel",
                return_value=mock_model
            ):
                with patch(
                    "collector.sys.stdin.readline",
                    side_effect=[
                        "getnext\n",
                        f"{current_oid}\n",
                        KeyboardInterrupt
                    ]
                ):
                    with patch(
                        "collector.sys.stdout",
                        fake_stdout
                    ):
                        with self.assertRaises(KeyboardInterrupt):
                            collector.main()

        self.assertEqual(
            fake_stdout.getvalue().strip(),
            "NONE"
        )

        mock_model.get_next_metric.assert_called_once_with(
            current_oid
        )

    def test_valid_command(self):
        self.assertTrue(collector.is_valid_command("get"))


    def test_invalid_command(self):
        self.assertFalse(collector.is_valid_command("DROP TABLE"))


    def test_valid_oid(self):
        self.assertTrue(
            collector.is_valid_oid(".1.3.6.1.4.1.99999.1.1")
        )


    def test_invalid_oid(self):
        self.assertFalse(
            collector.is_valid_oid("hello")
        )

if __name__ == "__main__":
    unittest.main()