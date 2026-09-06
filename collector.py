#!/data/BenHome/Code/snmp/.venv/bin/python

import json
import sys
from pathlib import Path
import logging
from time import time

###############################################################################
# Globals
###############################################################################

# Metrics for the collector
COLLECTOR_STATUS_OID = '.1.3.6.1.4.1.99999.0.1'
COLLECTOR_AGE_OID = '.1.3.6.1.4.1.99999.0.2'

COLLECTOR_START_TIME = int(time())
COLLECTOR_STATUS = 1 # 0: Down, 1:Up, 2:Error

# Global list of OIDs used by getnext
SORTED_OIDS = [COLLECTOR_STATUS_OID, COLLECTOR_AGE_OID]

# Files
SCRIPT_DIR = Path(__file__).resolve().parent
DATA_FILE = SCRIPT_DIR / "metrics.json"
LOG_FILE = SCRIPT_DIR / f"{Path(__file__).name}.log"

# Set up logging ##############################################################
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

# loads the metric.json file into a dict
def load_metrics():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)

    except Exception:
        COLLECTOR_STATUS = 2 # No Metrics file to load
        return {}


def get_metric_for_oid(oid):

    logger.debug(f"OID: {oid}")

    if oid == COLLECTOR_STATUS_OID:
        return (
            oid,
            "integer",
            get_collector_status()
        )

    if oid == COLLECTOR_AGE_OID:
        return (
            oid,
            "integer",
            get_collector_age()
        )

    metrics = load_metrics()
    metric = metrics.get(oid)

    if metric is None:
        return None

    return (
        oid,
        metric["datatype"],
        metric["value"]
    )


def get_next_oid(current_oid):

    for oid in SORTED_OIDS:
        if oid > current_oid:
            return oid

    return None


# Returns metric related to the collector
def get_collector_age():
    return int(time()) - COLLECTOR_START_TIME


# Returns metric related to the collector
def get_collector_status():
    return COLLECTOR_STATUS


def setup():
    # Get an ordered list of keys on startup, NOTE: this means the metric 
    # file must have data when Net-SNMP is started

    SORTED_OIDS.extend( list( load_metrics().keys() ) )
    SORTED_OIDS.sort()

    logger.debug(f"loaded OIDs: {SORTED_OIDS}")


###############################################################################
# Main
###############################################################################

def main():

    setup()

    logger.info("READY")
    sys.stdout.flush()

    while True:

        command = sys.stdin.readline().strip()

        if command == "PING":
            logger.debug("command: PING")
            logger.debug("output: PONG")

            print("PONG")
            sys.stdout.flush()
            continue

        if command == "get":
            logger.debug("command: get")

            oid = sys.stdin.readline().strip()
            result = get_metric_for_oid(oid)

            if result is None:
                logger.debug("NONE")

                print("output: NONE")

            else:
                oid, dtype, value = result
                logger.debug(f"output: {oid, dtype, value}")

                print(oid)
                print(dtype)
                print(value)

            sys.stdout.flush()

        elif command == "getnext":
            logger.debug("command: getnext")

            oid = sys.stdin.readline().strip()
            next_oid = get_next_oid(oid)

            if next_oid is None:
                logger.debug("output: NONE")

                print("NONE")

            else:
                result = get_metric_for_oid(next_oid)

                if result is None:
                    logger.debug("output: NONE")

                    print("NONE")

                else:
                    oid, dtype, value = result
                    logger.debug(f"output: {oid, dtype, value}")

                    print(oid)
                    print(dtype)
                    print(value)

            sys.stdout.flush()

if __name__=="__main__":
    main()