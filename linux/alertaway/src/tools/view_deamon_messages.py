import sys
from pathlib import Path

# This line ensures Geany can always find files in the src/ folder
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import systemd_install

# Your original code continues below...



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

services = systemd_install.list_of_systemd()
i = 0
for s in services:
    print (f"{i} {s}")
    i +=1
print ("pick one")
one = input()
print (services[int(one)])
result = journal(services[int(one)])
print(result)
