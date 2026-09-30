#!/usr/bin/python
import sys
import subprocess
import json

DATA_FILE = "metrics.json"

SERVICES = [ 'RT Process', 'tcsaim','RTPIF' ] # Note: much match app coord EXACTLY!

def run_system_command(service):
        try:
            args = ['/users/bin/priority_app_server', '-a', service]
            result = subprocess.run(args, timeout=5, stderr=subprocess.PIPE, stdout=subprocess.PIPE, encoding='utf-8')

            if result.returncode != 0:
                print(f"Non 0 return code from /users/bin/priority_app_server - {result.stderr}")

            else:
                return result.stdout

        except subprocess.TimeoutExpired as err:
            # Took too long, so app is probably not running, therefore: Not priority
            print("Timeout expired")
            exit(1)

        except Exception as err:
            # Some other error
            print(f"Failed to check connected clients - {err}")
            exit(1)


def is_priority_server(service):
    result = run_system_command(service)
    
    if result == 'TRUE\n':
        return True
    elif result.stdout == 'FALSE\n':
        return False
    else:
        print(f"Unexpected Output from /users/bin/priority_app_server\n{result.stdout}")
        sys.exit(1)


def export_metrics(data):
    try:
        with open(DATA_FILE, "w") as f:
            f.write(json.dumps(data, indent=4))
            return
    
    except Exception as err:
        print(f"Failed to write to file: {err}")
        sys.exit(1)


def main():

    data = {}

    for service in SERVICES:
        if is_priority_server(service):
            result = 1
        else:
            result = 0

        data[service.replace(" ", "").lower()] = result

    export_metrics(data)

    print("DONE")
    sys.exit(0)


if __name__=="__main__":
    main()