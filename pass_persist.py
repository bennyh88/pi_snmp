#!/data/BenHome/Code/snmp/.venv/bin/python

import json
import sys
import yaml
from pathlib import Path
import logging

SCRIPT_DIR = Path(__file__).resolve().parent

CONFIG_FILE = SCRIPT_DIR / "metrics.yml"

DATA_FILE = SCRIPT_DIR / "metrics.json"

LOG_FILE = SCRIPT_DIR / "log.log"


logger = logging.getLogger("pass_persist")
logger.setLevel(logging.DEBUG)

handler = logging.FileHandler(LOG_FILE, mode="w")
handler.setLevel(logging.DEBUG)

formatter = logging.Formatter(
    "%(asctime)s %(levelname)-8s %(message)s"
)

handler.setFormatter(formatter)
logger.addHandler(handler)

logger.info("Pass persist script starting")

def load_config():

    with open(CONFIG_FILE, "r") as f:
        return yaml.safe_load(f)["metrics"]


def load_metrics():

    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)

    except Exception:
        return {}


METRIC_CONFIG = load_config()
logger.debug(METRIC_CONFIG)

# Build mappings

OID_TO_METRIC = {}
METRIC_TO_OID = {}

for metric_name, config in METRIC_CONFIG.items():

    oid = config["oid"]

    OID_TO_METRIC[oid] = metric_name
    METRIC_TO_OID[metric_name] = oid


SORTED_OIDS = sorted(
    OID_TO_METRIC.keys(),
    key=lambda x: [int(i) for i in x.split(".")[1:]]
)

logger.debug(SORTED_OIDS)


def get_metric_for_oid(oid):

    metrics = load_metrics()

    metric_name = OID_TO_METRIC.get(oid)

    if metric_name is None:
        return None

    value = metrics.get(metric_name)

    if value is None:
        return None

    metric_config = METRIC_CONFIG[metric_name]

    return (
        oid,
        metric_config["type"],
        value
    )


def get_next_oid(current_oid):

    for oid in SORTED_OIDS:

        if oid > current_oid:
            return oid

    return None


logger.info("READY")
sys.stdout.flush()

while True:

    command = sys.stdin.readline().strip()

    if command == "PING":
        logger.debug("command = PING")
        logger.debug("PONG")
        print("PONG")
        sys.stdout.flush()
        continue

    if command == "get":
        logger.debug("command = get")

        oid = sys.stdin.readline().strip()

        result = get_metric_for_oid(oid)

        if result is None:
            logger.debug("NONE")
            print("NONE")

        else:

            oid, dtype, value = result
            logger.debug("oid, dtype, value")
            print(oid)
            print(dtype)
            print(value)

        sys.stdout.flush()

    elif command == "getnext":
        logger.debug("command = getnext")

        oid = sys.stdin.readline().strip()

        next_oid = get_next_oid(oid)

        if next_oid is None:
            logger.debug("NONE")
            print("NONE")

        else:

            result = get_metric_for_oid(next_oid)

            if result is None:
                logger.debug("NONE")
                print("NONE")

            else:

                oid, dtype, value = result
                logger.debug("oid, dtype, value")
                print(oid)
                print(dtype)
                print(value)

        sys.stdout.flush()