# MIT licence 2025  Jim Dodgen
# creates service files using tunnel_cfg.py to hide stuff from github checked in files
# so you need to create tunnel_cfg.py see below:
#
import cfg
import os
example = '''
# example tunnel_cfg.py
password = "password"
port = "9009" # what ever port number you are replicating
user = "user"
ip_addr = "1.2.3.4"
service_file_name = "autossh-vps-9009.service"
location_of_check_tunnel_and_restart.py = "/home/your_name/"
'''

systemd_path = "/etc/systemd/system/"


wd_name = "watchdog_tunnel.service"
watch_dog = '''
[Unit]
Description=check and restart tunnel service
StartLimitIntervalSec=0

[Service]
User=root
ExecStart=/usr/bin/python3 %scheck_tunnel_and_restart.py
Restart=on-failure
RestartSec=60

[Install]
WantedBy=multi-user.target
''' % (cfg.location_of_check_tunnel_and_restart)

print("=====\n%s\n=====\nInstall service? must be root (y,N)" % (watch_dog))
ans = input()
if (ans.upper() == "Y"):
    with open(systemd_path+wd_name,"w") as text_file:
        text_file.write(watch_dog)
    os.system(f"systemctl stop {wd_name}")
    os.system("systemctl daemon-reload")

    os.system(f"systemctl start {wd_name}")
    os.system(f"systemctl enable {wd_name}")

    os.system(f"systemctl status {wd_name}")
    os.system(f"journalctl -f -u {wd_name}")
