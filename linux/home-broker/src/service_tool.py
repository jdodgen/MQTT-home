# MIT licence 2026  Jim Dodgen
# this runs home-broker part of alertaway
# main.py manages the forked processes
import os

def install():
    service_name = "home_broker.service"
    systemd_path = "/etc/systemd/system/"
    print("installing service:", service_name)
    service = '''\
[Unit]
Description=home-broker main.py runs the subprocesses
After=network.target
StartLimitIntervalSec=0

[Service]
User=root
WorkingDirectory=%s
ExecStart=/usr/bin/python3 %s/main.py
RestartSec=30  
 
[Install]
WantedBy=multi-user.target
    ''' % (os.getcwd(), os.getcwd())
    print("=====\n%s\n=====\nInstall service? must be root (y,N)" % (service))
    ans = input()
    if (ans.upper() == "Y"):
        with open(systemd_path+service_name,"w") as text_file:
            text_file.write(service)
        os.system(f"systemctl stop {service_name}")
        os.system("systemctl daemon-reload")

        os.system(f"systemctl start {service_name}")
        os.system(f"systemctl enable {service_name}")

        os.system(f"systemctl status {service_name}")
        os.system(f"journalctl -f -u {service_name}")
    

if __name__ == "__main__":
    install()
