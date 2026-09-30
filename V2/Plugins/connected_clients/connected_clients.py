#!/usr/bin/python
import sys
import subprocess
import json

DATA_FILE = "metrics.json"

OPERATOR_CLASSES = [
    "Field Engineer",
    "Telecontrol Engineer",
    "Telecontrol Technician",
    "View Only",
    "Data Admin",
    "Dispatch Manager",
    "Control Engineer EHV",
    "Scada Commission Engineer",
    "Scheduler",
    "Call Taker",
    "Dispatcher",
    "Field Engineer Plus",
    "Control Engineer LV",
    "Control Engineer Plus",
    "Drawing Office",
    "Control Support",
    "System Manager",
    "Symbol Admin",
    "Report Admin",
    "Fault Manager",
    "Geoview",
    "Outage Planner",
    "Storm CallTaker",
    "System Admin",
    "Supp Message Team",
    "Alarm Manager",
    "Asset Management TLR",
    "Paknet Project",
    "DSO Engineer",
    "Vegetation Manager",
    "Tele Commissioning Technician",
    "Planner",
    "Asset Management Editor",
    "HV Switching Commissioning Eng",
    "Field Engineer RTU",
    "Control Engineer Remote",
    "Tele Commissioning Engineer"
]


def run_system_command():
        try:
            args = ['/users/bin/clients', '-f']
            result = subprocess.run(args, timeout=5, stderr=subprocess.PIPE, stdout=subprocess.PIPE, encoding='utf-8')

            if result.returncode != 0:
                print(f"Non 0 return code from /users/bin/clients - {result.stderr}")

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


def export_metrics(data):
    try:
        with open(DATA_FILE, "w") as f:
            f.write(json.dumps(data, indent=4))
            return
    
    except Exception as err:
        print(f"Failed to write to file: {err}")
        sys.exit(1)


def main():
    result = run_system_command()
    lines = result.splitlines()
    lines = lines[3:] # Remove Blank row, Header and Seperator lines

    data = {}
    
    data["total"] = len(lines)

    count_sorted = 0
    for operator_class in OPERATOR_CLASSES:
        count = 0
        for line in lines:
            if operator_class in line:
                count += 1

        data[operator_class.replace(" ", "")] = count
        count_sorted += count

    
    data["other"] = data["total"] - count_sorted

    export_metrics(data)

    print("DONE")
    sys.exit(0)



if __name__=="__main__":
    main()