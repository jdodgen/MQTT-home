from ipcqueue import posixmq
import const
import time
import threading
import zlib
import json
import sqlite3

class mqtt_task():
    def __init__(self, queue=None, my_parent=None):
    # keep device features updated in the data base 
    # handle the subscribe to the home-broker devices
    # for each subscribe callback compare to previous
    # update differences only NO state information
    import message
    import queue   # python queue not POSIX
    db = sqlite3.connect(const.db_name, timeout=const.db_timeout)
		
    q = queue.Queue() # callbacks are sent here
    msg = message.message(q) # MQTT connection tool# 

    msg.subscribe(const.home_MQTT_devices)
    #msg.publish(const.zigbee2mqtt_bridge_devices, 
    while True:
        (action, topic, payload) = q.get()
        if (action == "callback"):
            if (topic == const.home_MQTT_devices):
                check_and_refresh_devices(db,payload)
            else: # other topics are from device subscribes
                update_device_state(db,topic,payload)



    msg.publish("message_unit_test/demo_wall/set", '{"state": "on"}')
    msg.subscribe("message_unit_test/demo_wall/#")
    time.sleep(2) # prettier  output
    # this handles callbacks from above
previous_devices_dictionary = None


def check_and_refresh_devices(db,payload):
    global previous_devices_dictionary
    unzipped = zlib.decompress(payload)
    devices_dictionary = json.loads(unzipped)
    if previous_devices_dictionary == None:
        previous_devices_dictionary = devices_dictionary
    compare_and_update(db,devices_dictionary, previous_devices_dictionary)

    #list_all_devices(devices_dictionary)


# simple device dump/print
# # designed to load/update two tables
# a devices table and a features table
# a device has 1 or more features.
# Each feature contains the proper pub/sub strings
# no status information is included or ever will be.  
def list_all_devices(dev):
    all_devices = dev["devices"]
    print("\nDEVICES\n")
    for d in all_devices:
        print(d)
    print("\nFEATURES\n")
    all_features = dev["features"]
    for f in all_features:
        print(f)


FEATURES = "features"
def compare_and_update(db,current, previous):
    print(current)
    for friendly_name in (current.keys()):
        print(friendly_name)
        if friendly_name in previous:  # different
            if (current[friendly_name]['description'] != previous[friendly_name]['description'] or
               current[friendly_name]['date'] != previous[friendly_name]['date'] or
               current[friendly_name]['source'] != previous[friendly_name]['source']):
               update_device(db, friendly_name, current);
            elif FEATURES in current[friendly_name]:  # has features check for changes
                for feature in (current[friendly_name][FEATURES].keys()):  # each feature
                    print("\t", feature)
                    current_feature =   current[friendly_name][FEATURES][feature]
                    previous_feature = previous[friendly_name][FEATURES][feature]
                    print(current_feature)
                    for tag in (current_feature.keys():
                        if current_feature[tag] != previous_feature[tag]:
                            update_feature(db, friendly_name, current_feature);           
        else:
            insert_device(db, current)

def insert_device(device):
    print(device)
    
def update_device(device):
    print(device)                 
    

def update_device_state(db,topic,state):
    pass

if __name__ == "__main__":
    mqtt_task()
