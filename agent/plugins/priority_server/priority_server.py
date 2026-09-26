from metric import Metric, MetricType
from metric_set import MetricSet
from plugin_base import PluginBase
from plugin_error import MetricCollectionError

import subprocess


class Plugin(PluginBase):

    services: list[str] = ['RT Process', 'tcsaim','RTPIF'] # Note: much match app coord EXACTLY!

    def __init__(self):
        print(f"Plugin {self.name} Initialised")

    @property
    def name(self) -> str:
        return "priority_server"

    def collect(self) -> dict:
        return {
            "priority_server_rtprocess": self.is_priority_server('RT Process'),
            "priority_server_tcsaim" : self.is_priority_server('tcsaim'),
            "priority_server_rtpif" : self.is_priority_server('RTPIF'),
        }

    # Just for testing
    def is_priority_server(self, service):
        return 1




    
    
    # def is_priority_server(self, service):
    #     try:
    #         args = ['/users/bin/priority_app_server', '-a', service]
    #         result = subprocess.run(args, timeout=5, stderr=subprocess.PIPE, stdout=subprocess.PIPE, encoding='utf-8')

    #         if result.returncode != 0:
    #             raise MetricCollectionError(
    #                 plugin_name="priority_server",
    #                 metric_name=service,
    #                 message="Non 0 return code from /users/bin/priority_app_server"
    #             )
    #         else:
    #             if result.stdout == 'TRUE\n':
    #                 return True
    #             elif result.stdout == 'FALSE\n':
    #                 return False
    #             else:
    #                 # logger.error(f'is_priority_server - Unexpected Output from /users/bin/priority_app_server\n{result.stdout}')
    #                 raise MetricCollectionError(
    #                     plugin_name="priority_server",
    #                     metric_name=service,
    #                     message=f"Unexpected Output from /users/bin/priority_app_server\n{result.stdout}"
    #                 )

    #     except subprocess.TimeoutExpired as err:
    #         # Took too long, so app is probably not running, therefore: Not priority
    #         return False

    #     except Exception as err:
    #         # Means the program never ran
    #         raise MetricCollectionError(
    #             plugin_name="priority_server",
    #             metric_name=service,
    #             message=f"Failed to check priority server - {err}"
    #         )