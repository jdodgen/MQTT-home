'''MIT License

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
import fauxmo_manager
import mosquitto_manager
import zigbee2mqtt_manager
import mqtt_service_task
import load_zigbee_data
import const
import database
import http_server
import time
import os

from multiprocessing import Queue, active_children
from queue import Empty
#
# conditional print
import os 
my_name = os.path.basename(__file__).split(".")[0]
xprint = print # copy print
def print(*args, **kwargs): # replace print
    #return
    xprint("["+my_name+"]", *args, **kwargs) # the copied real print
#
#
if __name__ == "__main__":
    # not working os.nice(-1)   # HTTP thread needs this
    print("home-broker starting: Version[%s]" % (const.version,))
    time.sleep(20) # a pause to read above
    mqtt_queue = Queue()
    watch_dog_queue = Queue()
    database.database() #just to get tables created if needed
    
    mosquitto_task = None
    mqtt_task = None
    fauxmo_task = None 
    zigbee_task = None 
    http_thread = None 

    # process watchdog starting now
    watch_dog_queue.put(["test_message",0])
    print("entering start/watchdog loop")
    time.sleep(2)
    while True:
        # this runs once to start all proceses
        if not mosquitto_task or not mosquitto_task.is_alive():
            mosquitto_task=mosquitto_manager.start_mosquitto_task()
            print("watchdog mosquitto_task needs to be started")

        if not fauxmo_task or not fauxmo_task.is_alive():
            fauxmo_task = fauxmo_manager.start_fauxmo_task()
            print("watchdog fauxmo_task needs to be started")
        
        if not mqtt_task or not mqtt_task.is_alive():
            print("watchdog mqtt_task needs to be started")
            mqtt_task   = mqtt_service_task.start_MQTT_service_task(mqtt_queue)

        if not zigbee_task:
            zigbee_task = zigbee2mqtt_manager.start_zigbee2mqtt_task(watch_dog_queue)
            print("watchdog zigbee_task needs to be started")
            load_zigbee_data.ZigbeeDeviceRefresher()

        if not http_thread or not http_thread.is_alive():
            http_thread = http_server.start_http_task(fauxmo_task, watch_dog_queue)
            print("watchdog http_thread needs to be started")

        # now looping
            
        try:
            item = watch_dog_queue.get(timeout=const.watch_dog_queue_timeout)
        except Empty : # timed out
            continue # so loop
        except Exception as e: 
            print(e)
            continue
        else:
            # got something
            print(item)
            (command, oprand) = item
            print("watch_dog_queue [%s]" % (command,))
            if command == "startfauxmotask":
                # comes from http_server.py after a restart request
                fauxmo_task = None # this cause it to be started
            elif command == "shutdown":
                active = active_children()
                for child in active:
                    print("terminating")
                    child.terminate()
                os._exit(-1)
        