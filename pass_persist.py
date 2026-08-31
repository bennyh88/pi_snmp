#!/usr/bin/env python3

import json
import sys
import yaml
from pathlib import Path

CONFIG_FILE = Path(
    "/opt/ukpn-monitor/config/metrics.yml"
)

DATA_FILE = Path(
    "/opt/ukpn-monitor/data/metrics.json"
)


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


print("READY")
sys.stdout.flush()

while True:

    command = sys.stdin.readline().strip()

    if command == "PING":

        print("PONG")
        sys.stdout.flush()
        continue

    if command == "get":

        oid = sys.stdin.readline().strip()

        result = get_metric_for_oid(oid)

        if result is None:
            print("NONE")

        else:

            oid, dtype, value = result

            print(oid)
            print(dtype)
            print(value)

        sys.stdout.flush()

    elif command == "getnext":

        oid = sys.stdin.readline().strip()

        next_oid = get_next_oid(oid)

        if next_oid is None:

            print("NONE")

        else:

            result = get_metric_for_oid(next_oid)

            if result is None:

                print("NONE")

            else:

                oid, dtype, value = result

                print(oid)
                print(dtype)
                print(value)

        sys.stdout.flush()