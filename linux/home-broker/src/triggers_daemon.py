# MIT licence 2025 Jim Dodgen
version = 0.1

import time
import suntime
import datetime
from dateutil import tz
import asyncio
import multiprocessing
import cfg
# import mqtt_manager
import message
import database

xprint = print # copy print
my_name = "[timers_daemon]"
def print(*args, **kwargs): # replace print
    #return  # comment/uncomment to turn print on off
    # do whatever you want to do
    #xprint('statement before print')
    xprint(my_name, *args, **kwargs) # the copied real print

def main():
    db = database.database()
    q = queue.Queue()  
    msg = message.message(q, my_parent=my_name)
    subscribes = db.get_triggers_subscribes()
    for sub in subscribes;
        msg.client.subscribe(sub, 0)
    while True:
        try:
            item = q.get(timeout=20)
        except queue.Empty:
            print("triggers_deamon empty sleeping")
            continue
        if item is None:
            print("ZigbeeDeviceRefresher: no reply from ", self.topic)
            break
        print("ZigbeeDeviceRefresher item[0] [%s]" % (item[0],))
        if item[0] == "callback":
			
            if item[1] == const.zigbee2mqtt_bridge_devices: # reply topic
                load_database_from_zigbee(item[2])
                ##  break
        
def task():
    main()
     
def start_timers_daemon():
    p = multiprocessing.Process(target=task)
    p.start()
    return p
    
    

if __name__ == "__main__":
    # Run the main coroutine as the entry point of the asyncio program
    asyncio.run(main())
