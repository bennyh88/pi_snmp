#!/data/BenHome/Code/snmp/.venv/bin/python

import json
import sys
import yaml
from pathlib import Path
import logging
from time import time

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


###############################################################################
# Main
###############################################################################

def main():
    logger.debug("main started")
    print("main started")

    metrics = get_agent_metrics()
    export_metrics(metrics)



if __name__=="__main__":
    main()