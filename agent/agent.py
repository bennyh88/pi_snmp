#!/data/BenHome/Code/snmp/.venv/bin/python
from metric import Metric, MetricType
from metric_set import MetricSet

import json
import sys
import yaml
from pathlib import Path
import logging
from time import time
import importlib
from plugin_base import PluginBase
from metric_model import MetricModel

###############################################################################
# Globals
###############################################################################

# Metrics for the Agent
AGENT_STATUS_OID = '.1.3.6.1.4.1.99999.0.3'
AGENT_AGE_OID = '.1.3.6.1.4.1.99999.0.4'

AGENT_START_TIME = int(time())
AGENT_STATUS = 1 # 0: Down, 1:Up, 2:Error

# Files
SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_FILE = SCRIPT_DIR / "metrics.yml"
DATA_FILE = SCRIPT_DIR / "metrics_tmp.json"
LOG_FILE = SCRIPT_DIR / f"{Path(__file__).name}.log"

# Logging
logger = logging.getLogger(Path(__file__).name)
logger.setLevel(logging.DEBUG)

handler = logging.FileHandler(LOG_FILE, mode="w")
handler.setLevel(logging.DEBUG)

formatter = logging.Formatter(
    "{asctime} {levelname:<8}{funcName:>22}():{lineno:<5}- {message}",
    style = "{"
)

handler.setFormatter(formatter)
logger.addHandler(handler)

logger.info("Collector Initialising")


###############################################################################
# Functions
###############################################################################

# Returns metric related to the collector
def get_agent_age():
    return int(time()) - AGENT_START_TIME


# Returns metric related to the collector
def get_agent_status():
    return AGENT_STATUS


def get_agent_metrics():
    metrics = {}

    metrics[AGENT_STATUS_OID] = {
        "name":"agent_status",
        "value": get_agent_status(),
        "datatype": "integer"
    }

    metrics[AGENT_AGE_OID] = {
        "name":"agent_age",
        "value": get_agent_age(),
        "datatype": "integer"
    }

    return metrics


def export_metrics(metrics):
    try:
        with open(DATA_FILE, "w") as f:
            #json.dump(metrics, f)
            f.write(json.dumps(metrics, indent=4))
            return
    
    except Exception:
        COLLECTOR_STATUS = 2 # Failed to Open metric file
        return {}

# Reads in YAML file to create config object
def read_config():
    with open(CONFIG_FILE, "r") as f:
        config = yaml.safe_load(f)
    return config["config"]


def parse_config(config):
    
    base_oid = config["base_oid"]

    for plugin in config["plugins"]:
        plugin_metrics = []
        plugin_oid = config["plugins"][plugin]["plugin_oid"]

        for metric in config["plugins"][plugin]["metrics"]:
            metric_oid = config["plugins"][plugin]["metrics"][metric]["oid"]

            plugin_metrics.append(
                Metric(
                    name=metric,
                    metric_type=config["plugins"][plugin]["metrics"][metric]["datatype"],
                    oid=f"{base_oid}.{plugin_oid}.{metric_oid}"
                )
            )

        metric_set = MetricSet(
            plugin_name=plugin,
            metrics=plugin_metrics
        )

        print(json.dumps(metric_set.to_dict(), indent=4))

def parse_config(config):
    
    base_oid = config["base_oid"]

    for plugin in config["plugins"]:
        plugin_metrics = []
        plugin_oid = config["plugins"][plugin]["plugin_oid"]

        for metric in config["plugins"][plugin]["metrics"]:
            metric_oid = config["plugins"][plugin]["metrics"][metric]["oid"]

            plugin_metrics.append(
                Metric(
                    name=metric,
                    metric_type=config["plugins"][plugin]["metrics"][metric]["datatype"],
                    oid=f"{base_oid}.{plugin_oid}.{metric_oid}"
                )
            )

        metric_set = MetricSet(
            plugin_name=plugin,
            metrics=plugin_metrics
        )

        print(json.dumps(metric_set.to_dict(), indent=4))


def init_plugin(plugin_name):

    module =  importlib.import_module(
        f"plugins.{plugin_name}.{plugin_name}"
    )

    plugin_class = getattr(module, "Plugin")
    plugin = plugin_class()

    return plugin
    

def get_plugin_metrics():
    metrics = {}

    for plugin in plugins:
        metrics.update(plugin.collect())
    
    return metrics
    


###############################################################################
# Setup, run once on startup
###############################################################################

metric_mapping = {}

# Will hold instances of all the plugins loaded
plugins: list[PluginBase | None] = []

def setup():
    logger.debug("setup")
    print("setup")

    # Read in config from YAML file
    config = read_config()

    # 
    metric_model = MetricModel(config)


    # Initialse Plugins
    for plugin in config["plugins"]:
        if plugin != 'builtin':
            logger.debug(f"Initialising PLugin: {plugin}")
            plugins.append(init_plugin(plugin))

    

    

    


###############################################################################
# Main
###############################################################################

def main():
    setup()

    logger.debug("main started")
    print("main started")

    metrics = get_plugin_metrics()
    # metrics = get_agent_metrics()
    export_metrics(metrics)



if __name__=="__main__":
    main()