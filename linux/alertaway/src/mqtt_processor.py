from ipcqueue import posixmq
import const
import time
import threading
import zlib
import json
import sqlite3
import message
import queue   # python queue not POSIX
import copy

current = None
previous = None
print("None", type(previous), type(current))
topic_to_device_feature = {}

def mqtt_task():
    global previous
    print("mt", type(previous), type(current))
    # keep device features updated in the data base 
    # handle the subscribe to the home-broker devices
    # for each subscribe callback compare to previous
    # update differences only NO state information
    previous = None
    print("mt2", type(previous), type(current))
    db = sqlite3.connect(const.db_name, timeout=const.db_timeout)
    check = check_and_refresh_devices(db)	
    updates = device_state(db)
    q = queue.Queue() # callbacks are sent here
    msg = message.message(q) # MQTT connection tool# 
    msg.subscribe(const.home_MQTT_devices)
    while True:
        (action, topic, payload) = q.get()
        if (action == "callback"):
            print("callback",type(topic), type(payload))
            if (topic == const.home_MQTT_devices):
                check.compare_and_update(payload)
            else: # other topics are from device subscribes
                updates.update(topic,payload)

    # example code
    msg.publish("message_unit_test/demo_wall/set", '{"state": "on"}')
    msg.subscribe("message_unit_test/demo_wall/#")
    time.sleep(2) # prettier  output
    # this handles callbacks from above

class check_and_refresh_devices():
    def __init__(self, db):
        self.db = db
        self.FEATURES = "features"

    def compare_and_update(self, payload):
        global current
        global previous
        print("glob", type(previous), type(current))
        unzipped = zlib.decompress(payload)
        current = json.loads(unzipped)
        print("loaded", type(previous), type(current))
        if previous is None:
            previous = copy.deepcopy(current)
            print("set previous",type(previous), type(current))
            self.check_current_against_database()
        print("check friendly name", type(previous), type(current),type(None))
        for friendly_name in (current.keys()):
            print(friendly_name)
            if friendly_name in previous:  # exists
                print(friendly_name, type(previous), type(current))
                #print("prev", previous[friendly_name] )
                if (current[friendly_name]['description'] != previous[friendly_name]['description'] or
                   current[friendly_name]['date']         != previous[friendly_name]['date'] or
                   current[friendly_name]['source']       != previous[friendly_name]['source']):
                    self.update_device(friendly_name, current);
                if self.FEATURES in current[friendly_name]:  # has features check for changes
                    for feature in (current[friendly_name][self.FEATURES].keys()):  # each feature
                        #print("\t", feature)
                        current_feature =   copy.deepcopy(current[friendly_name][self.FEATURES][feature])
                        previous_feature =  copy.deepcopy(previous[friendly_name][self.FEATURES][feature])
                        # print(current_feature)
                        for tag in current_feature.keys():
                            if current_feature[tag] != previous_feature[tag]:
                                self.update_feature(friendly_name, feature, current_feature);
                                break
            else:
                self.insert_device(friendly_name)

    def insert_device(self,friendly_name):
        global current
        cur = self.db.cursor()
        cur.execute('''insert into mqtt_devices (friendly_name, description, source, last_time)"
        values (?,?,?,?)''',
        friendly_name,
        current[friendly_name]['description'], 
        current[friendly_name]['date'],         
        current[friendly_name]['source'],
        self.now)
        cur.close()
        self.db.commit()
        if self.FEATURES in current[friendly_name]:  # has features check for changes
            for feature in (current[friendly_name][self.FEATURES].keys()):  # each feature
                f = current[friendly_name][self.FEATURES][feature]
                if f["access"] == "sub":  #device subscribes 
                    table = "publish_feature"
                else:
                    table = "subscribed_features"

                cur = self.db.cursor()
                cur.execute('''insert into mqtt_devices (friendly_name, description, source, last_time)"
                        values (?,?,?,?)''',
                friendly_name,
                feature,
                f[friendly_name]['description'], 
                f[friendly_name]['date'],         
                f[friendly_name]['source'],
                self.now)
                cur.close()
                self.db.commit()
        
    def update_device(self,friendly_name, current):
        print(friendly_name)                 
        
    def update_feature(self, friendly_name, feature, current_feature):
        global topic_to_device_feature
        # we build/rebuild the subscribed topic_to_device_feature
        # used when subscribe callbacks arrive
        print(type(current_feature))
        targets = []
        if (current_feature["access"] == "sub"):
            if current_feature["topic"] in topic_to_device_feature: 
                targets = topic_to_device_feature[current_feature["topic"]]
            targets.append([friendly_name, feature])
            topic_to_device_feature[current_feature["topic"]] = targets
        print(friendly_name, current_feature)
        # now update feature
    
    def check_current_against_database(self):
        print("check_current_against_database called")
        pass

class device_state():
    def __init__(self, db):
        self.db = db	
    def update(self, topic, state):
        pass
        
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


# test area        
if __name__ == "__main__":
    #mqtt_task()
    db = sqlite3.connect("test.db", timeout=const.db_timeout)
    check = check_and_refresh_devices(db)	
    with open("test_json.js", 'r') as file:
        json_1 = file.read()
        #print(type(json_1))
        #print(json_1)
    with open("test_json_with_changes.js", 'r', encoding='utf-8-sig') as file:
        json_2 = file.read()
    # sample payload 
    payload_1 = zlib.compress(bytes(json_1,'utf-8'))
    print(">>>>>>%s<<<<<<" % (json_1))
    previous = json.loads(json_1)
    print("\n\n test 1  check if equal")
    check.compare_and_update(payload_1)  
    print("\n\n test 2  check differences")
    # test 2 check when differences      
    previous  = json.loads(json_2)
    check.compare_and_update(payload_1)  
    print("\n\n test 3  check differences")
    # test 3 check when None previous, starting up for example
    # need to check against database, slower      
    check.compare_and_update(payload_1)  
                    
