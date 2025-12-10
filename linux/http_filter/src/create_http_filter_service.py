# MIT licence 2025  Jim Dodgen
# filters http request (from a tunnel) and based on data and does a fixed "requests" query returning results to caller
# so you need to create http_filter_cfg.py see below:
#
example = '''
# example http_filter_cfg.py
http_port = "9048"
valid_requests = ["driveway: "http://camera", "doorway": "http://camera",]
'''

systemd_path = "/etc/systemd/system/"

import os
import http_filter_cfg  # stuff to hide


http_filter = "http_filter.service"
service = '''
[Unit]
Description=http filter

[Service]
User=root
ExecStart=/usr/bin/python3 %shttp_filter.py"

[Install]
WantedBy=multi-user.target
''' % (tunnel_cfg.location_of_check_tunnel_and_restart)

with open(systemd_path+http_filter,"w") as text_file:
    text_file.write(service)


os.system("systemctl daemon-reload")

os.system("systemctl start "+http_filter)
os.system("systemctl enable "+http_filter)

os.system("systemctl status "+http_filter)
