from abc import ABC, abstractmethod

from metric_set import MetricSet


class PluginBase(ABC):

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def collect(self) -> MetricSet:
        pass