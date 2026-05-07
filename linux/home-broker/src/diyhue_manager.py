# diyhue_manager.py
'''
MIT License

Copyright (c) 2023,2024 Jim Dodgen

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''
import os
import subprocess
import time
import database
# import multiprocessing
#from message import our_ip_address
import http_common as config

BROKER_IP = config.get_db_config()["broker"]
#
# conditional print
my_name = "diyhue_manager"
xprint = print # copy print
def print(*args, **kwargs): # replace print
    #return
    xprint("["+my_name+"]", *args, **kwargs) # the copied real print
def print_always(*args, **kwargs): # replace print
    xprint("["+my_name+"]", *args, **kwargs) # the copied real print

def send_discovery_payloads() -> str:
    db = database.database()
    devices = db.get_fauxmo_devices()
    if len(devices) > 0:
        fauxmo_cfg = head % (config.MQTTPLUGIN)
        print("number of fauxmo devices[%s]" % (len(devices),))
        for dev in devices:
            print(f"dev[{dev}]")
            port = dev[0].replace('"','\\"') if type(dev[0]) == str else dev[0]
            name = dev[1].replace('"','\\"')
            topic = dev[2].replace('"','\\"')
            on_payload = dev[3].replace('"','\\"')
            try:
                off_payload = dev[4].replace('"','\\"')
            except:
                off_payload = None
            fauxmo_cfg = fauxmo_cfg + per_device_minimum % (port, name, topic,on_payload, topic, off_payload, BROKER_IP, config.get_db_config()["broker_mqtt_port"])
            fauxmo_cfg = fauxmo_cfg + use_fake_state  
            fauxmo_cfg = fauxmo_cfg + initial_state
     
            fauxmo_cfg = fauxmo_cfg[:-1] + end
        fauxmo_cfg = fauxmo_cfg[:-1] + tail
        print(fauxmo_cfg)
        return fauxmo_cfg
    else:
        return None

def task():
    print_always("task starting")
    while True:
        if send_discovery_payloads() != None:
            try:
                # process = subprocess.Popen([
                        # "/usr/local/bin/fauxmo", 
                        # "-c", config.FAUXMO_CONFIG_FILE_PATH, 
                        # "-vv"
                        # ])
                os.execl("/usr/local/bin/fauxmo", "-c " + config.FAUXMO_CONFIG_FILE_PATH, "-vv")
                # for testing  /usr/local/bin/fauxmo -c /etc/fauxmo/config.json   "
            except:
                pass
            # only returns if it fails
            print("ERROR: faxmo exited, waiting and restarting")
        else:
            pass
            print("No fauxmo devices")
        time.sleep(config.FAUXMO_SLEEP_SECONDS)  


if __name__ == "__main__":
   
    task()
    time.sleep(1000)
    #print(build_cfg())
   # task()
