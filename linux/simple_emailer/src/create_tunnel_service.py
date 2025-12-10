# MIT licence 2025  Jim Dodgen
# hiding stuff from github files

import tunnel_cfg
example = '''
# example tunnel_cfg.py
password = "password"
port = "9009" # what ever port number you are replicating
user = "user"
ip_addr = "1.2.3.4"
service_file_name = "autossh-vps-9009.service"
'''

service = '''
[Unit]
Description=Percistent tunnel
After=network.target

[Service]
User=simplenvr
ExecStart=/usr/bin/sshpass -p %s /usr/bin/autossh -M 0 -o "ExitOnForwardFailure=yes"  -o "ServerAliveInterval 30" -o "ServerAliveCountMax 3" -NR 0.0.0.0:%s:localhost:%s  %s@2%s

[Install]
WantedBy=multi-user.target
''' % (tunnel_cfg.password, tunnel_cfg.port, tunnel_cfg.port, tunnel_cfg.user, tunnel_cfg.ip_addr)

with open(tunnel_cfg.service_file_name, "w") as text_file:
    text_file.write(service)
