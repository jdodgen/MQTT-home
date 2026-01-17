# this was needed because /etc/systemd/system/autossh-vps???.service does not restart on a reboot when network interupted.

import urllib.request
import time
import os
import tunnel_cfg

url = "http://%s:%s" % (tunnel_cfg.ipaddr,tunnel_cfg.port)
check_sleep_time = 60*60
wait_sleep_time = 60*4
broke_wait_time = 60*60*4
restart = "systemctl restart "+tunnel_cfg.service_file_name
while True:
    try:
        while True:
            try:
                sock = urllib.request.urlopen(url) #, timeout=10)
            except:
                #print("not found")
                time.sleep(wait_sleep_time)
                os.system(restart)
            time.sleep(check_sleep_time)
    except:
         print("big fail")
         time.sleep(broke_wait_time)

