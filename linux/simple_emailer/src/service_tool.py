import os

def install():
    service_name = "simple_emailer.service"
    systemd_path = "/etc/systemd/system/"
    print("installing service", service_name)
    service = '''\
[Unit]
Description=Sends emails when reciving certain MQTT messages
After=network.target
StartLimitIntervalSec=0

[Service]
User=root
WorkingDirectory=%s
ExecStart=/usr/bin/python3 %s/send_emails.py
RestartSec=30  
 
[Install]
WantedBy=multi-user.target
    ''' % (os.getcwd(), os.getcwd())
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
