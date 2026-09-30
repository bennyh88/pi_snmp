
import yaml
from metric_model import MetricModel
from metric import Metric

import sys
from pathlib import Path
import logging
from time import time
#!/data/BenHome/Code/snmp/.venv/bin/python


###############################################################################
# Globals
###############################################################################

# Files
SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_FILE = SCRIPT_DIR / "metrics.yml"
LOG_FILE = SCRIPT_DIR / f"{Path(__file__).name}.log"

# Set up logging ##############################################################
logger = logging.getLogger(Path(__file__).name)
logger.setLevel(logging.DEBUG)

handler = logging.FileHandler(LOG_FILE, mode="w")
handler.setLevel(logging.DEBUG)

formatter = logging.Formatter(
    "{asctime} {levelname:<8}{funcName:>24}():{lineno:<5}- {message}",
    style = "{"
)

handler.setFormatter(formatter)
logger.addHandler(handler)

logger.info("Collector Initialising")

###############################################################################
# Functions
###############################################################################

# Reads in YAML file to create config object
def read_config() -> dict:
    try:
        with open(CONFIG_FILE, "r") as f:
            config = yaml.safe_load(f)
            return config["config"]
        
    except FileNotFoundError:
        logger.critical(f"Configuration file not found: {CONFIG_FILE}")
        sys.exit(1)

    except yaml.YAMLError as err:
        logger.critical(f"Invalid YAML in {CONFIG_FILE}: {err}")
        sys.exit(1)

    except KeyError:
        logger.critical(f"Missing 'config' section in {CONFIG_FILE}")
        sys.exit(1)

    except Exception:
        logger.exception(f"Unexpected error loading {CONFIG_FILE}")
        sys.exit(1)


def handle_ping() -> None:
    logger.debug("output: PONG")
    print("PONG")
    sys.stdout.flush()


def handle_get(metric_model: MetricModel, oid: str) -> None:
    metric = metric_model.get_metric(oid)
    write_metric(metric)


def handle_getnext(metric_model: MetricModel, oid: str) -> None:
    metric = metric_model.get_next_metric(oid)
    write_metric(metric)


def write_none() -> None:
    logger.debug("output: NONE")
    print("NONE")
    sys.stdout.flush()


def write_metric(metric: Metric | None) -> None:
    if metric is None:
        write_none()
        return

    logger.debug(f"output: {metric.oid, metric.datatype, metric.value}")

    print(metric.oid)
    print(metric.datatype)
    print(metric.value)
    sys.stdout.flush()


def is_valid_command(command: str) -> bool:
    return command in {"PING", "get", "getnext"}


def is_valid_oid(oid: str) -> bool:
    if not oid:
        return False

    return all(
        part.isdigit()
        for part in oid.lstrip(".").split(".")
    )


def read_input() -> str:
    input = sys.stdin.readline().strip()
    sys.stdout.flush()
    logger.debug(f"input: {input}")
    return input


def run(metric_model: MetricModel) -> None:
    # Enter infinite loop
    sys.stdout.flush()
    while True:

        command = read_input()

        if not is_valid_command(command):
            logger.warning(f"Invalid command received: {command}")
            continue

        if command == "PING":
            handle_ping()
            continue

        if command == "get":
            oid = read_input()

            if not is_valid_oid(oid):
                logger.warning(f"Invalid OID received: {oid}")
                write_none()
                continue

            handle_get(metric_model, oid)

        elif command == "getnext":
            oid = read_input()

            if not is_valid_oid(oid):
                logger.warning(f"Invalid OID received: {oid}")
                write_none()
                continue

            handle_getnext(metric_model, oid)


###############################################################################
# Main
###############################################################################

def main() -> None:

    # Read in Yaml file
    config = read_config()
        
    # Construct a metric model from config
    metric_model = MetricModel(logger, config)
    logger.debug(f"metric_model: \n{metric_model.to_string()}")

    logger.info("READY")
    run(metric_model)

if __name__=="__main__":
    main()
