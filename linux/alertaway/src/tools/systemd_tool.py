import sys
from pathlib import Path

# This line ensures finding files in  src/ folder aka  simple .. thank you python
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import systemd_install # needed for this

import subprocess

def journal(service_name):
    try:
        # Calls: sudo systemctl restart your_service.service

        subprocess.run(['/usr/bin/sudo', '/usr/bin/journalctl', '-u', service_name], check=True)
        # sudo journalctl -u alertaway-timers-daemon
        result = f"{service_name} restarted "
    except subprocess.CalledProcessError as e:
        result = f"Error restarting service: [{service_name}] {e}"
    return result

def systemctl (service_name, start_stop_status):
    try:
        # Calls: sudo systemctl restart your_service.service

        subprocess.run(['/usr/bin/sudo', '/usr/bin/systemctl ', start_stop_status, service_name], check=True)
        # sudo journalctl -u alertaway-timers-daemon
        result = f"{service_name} restarted "
    except subprocess.CalledProcessError as e:
        result = f"Error restarting service: [{service_name}] {e}"
    return result

services = systemd_install.list_of_systemd()
i = 0
for s in services:
    print (f"{i} {s}")
    i +=1
print ("pick one")
one = input()
service = services[int(one)]
print (service)
print("1)journalctl, 2)start, 3)stop, 4)status")
which = input()
if which == "1":
    result = journal(service)
elif which == "2":
    result = systemctl(service, "start")
elif which == "3":
    result = systemctl(service, "stop")
elif which == "4":
    result = systemctl(service, "status")
print(result)
