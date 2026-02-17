# MIT licence 2025  Jim Dodgen
import os

def install():
    service_name = "timers.service"
    systemd_path = "/etc/systemd/system/"
    print("installing service", service_name)
    service = '''\
[Unit]
Description=Publishes MQTT messages for predefined times, typicaly turrning off/on lights
After=network.target
StartLimitIntervalSec=0

[Service]
User=root
WorkingDirectory=%s
ExecStart=/usr/bin/python3 %s/timers_daemon.py
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
