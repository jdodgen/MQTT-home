from ipcqueue import posixmq
import const
import time
import threading
import zlib
import json

def device_features_task():  # keep device features updated in the data base 
    # handle the subscribe to the home-broker devices
    # for each subscribe callback compare to previous
    # update differences only NO state information
    import message
    import queue 
    q = queue.Queue() # callbacks are sent here
    msg = message.message(q) # MQTT connection tool# 

    msg.subscribe(const.home_MQTT_devices)
    #msg.publish(const.zigbee2mqtt_bridge_devices, 
    while True:
        (action, topic, payload) = q.get()
        if (action == "callback"):
            if (topic == const.home_MQTT_devices):
                check_and_refresh_devices(payload)
            else:
                update_device_state(topic,payload)


    msg.publish("message_unit_test/demo_wall/set", '{"state": "on"}')
    msg.subscribe("message_unit_test/demo_wall/#")
    time.sleep(2) # prettier  output
    # this handles callbacks from above
previous_devices_dictionary = None


def check_and_refresh_devices(payload):
    global previous_devices_dictionary
    unzipped = zlib.decompress(payload)
    devices_dictionary = json.loads(unzipped)
    if previous_devices_dictionary == None:
        previous_devices_dictionary = devices_dictionary
    compare_and_update(devices_dictionary, previous_devices_dictionary)

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
def compare_and_update(current, previous):
    print(current)
    for friendly_name in (current.keys()):
        print(friendly_name)
        if friendly_name in previous:  # it exists
            if (current[friendly_name]['description'] != previous[friendly_name]['description'] or
               current[friendly_name]['date'] != previous[friendly_name]['date'] or
               current[friendly_name]['source'] != previous[friendly_name]['source']):
               update_device_and_features(current);
            elif FEATURES in current[friendly_name]:  # has features check for changes
                for feature in (current[friendly_name][FEATURES].keys()):  # each feature
                    print("\t", feature)
                    print(current[friendly_name][FEATURES][feature])
                    for tag in (current[friendly_name][FEATURES][feature].keys():
                        if current[friendly_name][FEATURES][feature][tag] != previous[friendly_name][FEATURES][feature][tag]:
                            update_device_and_features(current);
                        
                    
        else:
            # insert it
            pass
        continue
        got_match = False
        for l in previous["devices"]:
            if l['friendly_name'] == d['friendly_name']:
                got_match = True    
                if (l['description'] != d['description'] or
                   l['date'] != d['date']):
                    print("different", d['friendly_name'])
                    changed_device(d)
                else:
                    #print("no diff",d['friendly_name'])
                    pass
                previous
        if got_match == False:
            print("found new one")
            new_device(d)

def new_device(device):
    print(device)
    
def update_device_and_features(device):
    print(device)                 
    

def update_device_state(topic,state):
    pass

if __name__ == "__main__":
    device_features_task()
