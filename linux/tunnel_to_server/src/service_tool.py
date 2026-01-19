# MIT Licence copyright 2025, 2026 Jim Dodgen
# this creates and installs a ssh tunnel to a server on the Internet
# 
import os
import cfg

def install():
    service_name = cfg.service_file_name
    systemd_path = "/etc/systemd/system/"
    print("installing [%s]\nservice:\n=====" % (service_name))
    ExecStart='''\
/usr/bin/sshpass -p "%s" \
/usr/bin/ssh -N -v \
-o "ExitOnForwardFailure=yes"  \
-o "StrictHostKeyChecking=no" \
-o "ServerAliveInterval=30" \
-o "ServerAliveCountMax=3" \
-R *:%s:127.0.0.1:%s  %s@%s''' % (cfg.password, cfg.port, cfg.port, cfg.remote_user, cfg.ip_addr) 
    print(ExecStart)
    service = '''\
[Unit]
Description=Persistent tunnel from local server to VPS
After=network-online.target
Wants=network-online.target
StartLimitIntervalSec=0
StartLimitBurst=0

[Service]
User=%s
ExecStart=%s
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
''' % (cfg.local_user, ExecStart)
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
