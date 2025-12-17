# MIT licence 2025  Jim Dodgen
# creates service files using tunnel_cfg.py to hide stuff from github checked in files
# so you need to create tunnel_cfg.py see below:
#

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

[Service]
User=root
ExecStart=/usr/bin/python3 %scheck_tunnel_and_restart.py"

[Install]
WantedBy=multi-user.target
''' % (tunnel_cfg.location_of_check_tunnel_and_restart)

with open(systemd_path+wd_name,"w") as text_file:
    text_file.write(watch_dog)


os.system("systemctl daemon-reload")

os.system("systemctl start wd_name")
os.system("systemctl enable wd_name")

os.system("systemctl status wd_name")
os.system("systemctl status "+tunnel_cfg.service_file_name)
