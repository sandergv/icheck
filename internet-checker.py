import os
import sys
import tempfile
import json

import datetime


PROJECT_PATH        = os.path.dirname(os.path.abspath(__file__))
USER                = os.getenv("USER")
HOME_PATH           = os.getenv("HOME")
DEFAULT_TIME        = 5
DATA_PATH           = f"{PROJECT_PATH}/InetChecker"
DATA_FILE           = f"{DATA_PATH}/icheck_events.json"
CONFIG_FILE         = f"{PROJECT_PATH}/icheck_config.json"
COMMENT             = "#icheck"
COMMAND             = f"python3 {PROJECT_PATH}/internet-checker.py check"


# VERSION
VERSION_MAJOR = 0
VERSION_MINOR = 1
VERSION_PATCH = 0


ARGS = sys.argv
ARGS.pop(0)


def show_help() -> None:
    pass


def get_version() -> str:
    return '.'.join(map(str, [VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH]))


def check_internet(host="8.8.8.8", port=53) -> bool:

    from socket import socket, AF_INET, SOCK_STREAM

    try:
        socket(AF_INET, SOCK_STREAM).connect((host, port))
        return True
    except Exception:
        return False


def get_arg(arg) -> str:

    if arg in ARGS:
        index = ARGS.index(arg)
        try:
            return ARGS[index+1]
        except:
            return None
    return None


def _get_cronjobs() -> list:

    from subprocess import Popen, PIPE

    
    process = Popen(['crontab', '-u', USER, '-l'], stdout=PIPE, stderr=PIPE)
    lines = process.stdout.readlines()
    return lines


def _job_exist() -> bool:

    for line in _get_cronjobs():
        if COMMENT in line.decode():
            return True

    return False


def set_job(time) -> None:  # only in minutes
    
    t = time if time < 59 and time > 0 else DEFAULT_TIME 

    if _job_exist():
        remove_job()

    jobs = _get_cronjobs()
    jobs.append(bytes(f"*/{t} * * * * {COMMAND} {COMMENT}\n".encode()))
    _write_jobs(jobs)


def remove_job() -> None:
    
    jobs = _get_cronjobs()

    for job in jobs:
        if COMMENT in job.decode():
            jobs.remove(job)

    _write_jobs(jobs)


def _write_jobs(jobs_list) -> None:

    from subprocess import run
    
    f, fp = tempfile.mkstemp()

    with os.fdopen(f, 'wb') as tmpf:
        for job in jobs_list:
            tmpf.write(job)
    tmpf.close()

    run(["crontab", "-u", USER, fp])
    os.remove(fp)


def get_datetime_obj(str_datetime) -> datetime.datetime:
    return datetime.datetime.strptime(str_datetime, '%Y-%m-%d %H:%M:%S')


def get_timestamp() -> str:
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def read_json(fp) -> dict:
    if os.path.isfile(fp):
        with open(fp, 'r') as f:
            d = json.load(f)
        f.close()
        return d
    else:
        return {}
    

def write_json(fp, data, merge=False) -> None:

    if os.path.isfile(fp):
        if merge:
            x = read_json(fp)
            z = {**x, **data}
            
            with open(fp, 'w') as f:
                json.dump(z, f, indent=2)
        else:
            with open(fp, 'w') as f:
                json.dump(data, f, indent=2)
                f.close()

    else:
        with open(fp, 'w+') as f: 
            json.dump(data, f, indent=2)
            f.close()



def init(time) -> None:
    
    if os.path.isfile(DATA_FILE):
        exit(0)

    if not os.path.isdir(DATA_PATH):
        os.makedirs(DATA_PATH)

    dt = get_timestamp()

    config_file = {
        "project_info": {
            "project_name": "icheck",
            "init_date": dt.split()[0],
            "init_time": dt.split()[1],
            "user": USER
        },
        "config": {
            "data_path": DATA_PATH,
            "check_interval": time
        }
    }
    data_file = {
        "events": [],
        "last_event": {}
    }

    first_event = {
        "date": dt.split()[0],
        "time": dt.split()[1],
        "state": check_internet()
    }

    data_file['events'].append(first_event)
    data_file['last_event'] = first_event
    set_job(time)
    write_json(CONFIG_FILE, config_file)
    write_json(DATA_FILE, data_file)


def show_events(opt) -> None:
    data_file = read_json(DATA_FILE)
    
    if opt == 'last':
        last_event = data_file['last_event']

        print(
            f"Fecha:\t{last_event['date']}\n"
            f"Hora:\t{last_event['time']}\n"
            f"Estado:\t{last_event['state']}\n"
        )

    else:
        print(data_file)


def check() -> None:
    
    json_data = read_json(DATA_FILE)
    
    state = check_internet()
    last_event = json_data['last_event']
    print(state)
    if last_event['state'] == state:
        exit(0)

    dt = get_timestamp()
    event = {
        "date": dt.split()[0],
        "time": dt.split()[1],
        "state": state,
    }
    # prev_event if the last event was False
    if not last_event['state']:
        event.update({"prev_event": last_event})

    json_data['events'].append(event)
    json_data['last_event'] = event
    write_json(DATA_FILE, json_data)


if __name__ == "__main__":

    opt = None

    try:
        opt = ARGS.pop(0)
    except IndexError:
        pass

    if opt == 'init':

        time = DEFAULT_TIME
        
        if '-t' in ARGS:
            time = int(get_arg('-t'))

        init(time=time)

    elif opt == 'events':

        if '-l' in ARGS:
            show_events('last')

    elif opt == 'check':
        check()

    elif opt == 'cron':
        
        if '-u' in ARGS:
            t = get_arg('-u')
            set_job(t)
        if '-r' in ARGS:
            remove_job()

    else:
        print(f'"{opt}" No es una opción valida.')
