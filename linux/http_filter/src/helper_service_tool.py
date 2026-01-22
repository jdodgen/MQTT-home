# MIT licence 2025  Jim Dodgen
import os

def install():
    service_name = "http_filter_restart.service"
    systemd_path = "/etc/systemd/system/"
    print("installing service", service_name)
    service = '''\
[Unit]
Description=http filter is restarted eachtime the tunnel fails 

[Service]
Type=oneshot
ExecStart=/bin/systemctl restart http_filter.service

[Install]
WantedBy=multi-user.target

'''
    print("=====\n%s\n=====\nInstall service? must be root (y,N)" % (service))
    ans = input()
    if (ans.upper() == "Y"):
        with open(systemd_path+service_name,"w") as text_file:
            text_file.write(service)
        '''os.system(f"systemctl stop {service_name}")
        os.system("systemctl daemon-reload")

        os.system(f"systemctl start {service_name}")
        os.system(f"systemctl enable {service_name}")

        os.system(f"systemctl status {service_name}")
        os.system(f"journalctl -f -u {service_name}")
    '''

if __name__ == "__main__":
    install()
