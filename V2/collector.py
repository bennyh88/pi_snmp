
import yaml
from metric_model import MetricModel

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
    "{asctime} {levelname:<8}{funcName:>22}():{lineno:<5}- {message}",
    style = "{"
)

handler.setFormatter(formatter)
logger.addHandler(handler)

logger.info("Collector Initialising")

###############################################################################
# Functions
###############################################################################

# Reads in YAML file to create config object
def read_config():
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


###############################################################################
# Main
###############################################################################

def main():

    # Read in Yaml file
    config = read_config()
        
    # Construct a metric model from config
    metric_model = MetricModel(logger, config)

    logger.debug(f"metric_model: \n{metric_model.to_string()}")

    logger.info("READY")

    # Enter infinite loop
    sys.stdout.flush()
    while True:

        command = sys.stdin.readline().strip()

        if command == "PING":
            logger.debug("command: PING")
            

            print("PONG")
            logger.debug("output: PONG")
            sys.stdout.flush()
            continue

        if command == "get":
            logger.debug("command: get")

            oid = sys.stdin.readline().strip()
            metric = metric_model.get_metric(oid)

            if metric is None:
                print("NONE")
                logger.debug("metric: NONE")

            else:
                print(metric.oid)
                print(metric.datatype)
                print(metric.value)

                logger.debug(f"output: {metric.oid, metric.datatype, metric.value}")
        
            sys.stdout.flush()

        elif command == "getnext":
            logger.debug("command: getnext")

            oid = sys.stdin.readline().strip()
            
            metric = metric_model.get_next_metric(oid)

            if metric is None:
                print("output: NONE")
                logger.debug("NONE")

            else:
                print(metric.oid)
                print(metric.datatype)
                print(metric.value)

                logger.debug(f"output: {metric.oid, metric.datatype, metric.value}")

            sys.stdout.flush()


if __name__=="__main__":
    main()