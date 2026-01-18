# this was needed because /etc/systemd/system/autossh-vps???.service does not restart on a reboot when network interupted.

import urllib.request
import time
import os
import cfg

url = "http://%s:%s" % (cfg.ip_addr,cfg.port)
print(url)
check_sleep_time = 60*60
wait_sleep_time = 60*4
broke_wait_time = 60*60*4
restart = "systemctl restart "+cfg.service_file_name
print(restart)
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

