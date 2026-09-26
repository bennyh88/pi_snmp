"""
plugin_error.py

Custom exceptions for the plugin framework.
"""


class PluginError(Exception):
    """Base class for all plugin-related exceptions."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class PluginLoadError(PluginError):
    """Raised when a plugin cannot be loaded."""


class PluginConfigError(PluginError):
    """Raised when plugin configuration is invalid."""


class PluginRegistrationError(PluginError):
    """Raised when plugin registration fails."""


class PluginExecutionError(PluginError):
    """Raised when a plugin fails during execution."""


class MetricCollectionError(PluginExecutionError):
    """Raised when metric collection fails."""

    def __init__(
        self,
        plugin_name: str,
        metric_name: str,
        message: str,
    ):
        self.plugin_name = plugin_name
        self.metric_name = metric_name

        super().__init__(
            f"Plugin '{plugin_name}' failed to collect "
            f"metric '{metric_name}': {message}"
        )


class MetricValidationError(PluginExecutionError):
    """Raised when a metric contains invalid data."""

    def __init__(
        self,
        plugin_name: str,
        metric_name: str,
        value,
        message: str,
    ):
        self.plugin_name = plugin_name
        self.metric_name = metric_name
        self.value = value

        super().__init__(
            f"Metric '{metric_name}' from plugin "
            f"'{plugin_name}' is invalid "
            f"(value={value!r}): {message}"
        )