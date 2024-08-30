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
#print("None", type(previous), type(current))
topic_to_device_feature = {}

# conditional print
xprint = print # copy print
def print(*args, **kwargs): # replace print
    # return
    xprint("[mqtt_processor]", *args, **kwargs) # the copied real print 

def mqtt_task():
    global previous
    #print("mt", type(previous), type(current))
    # keep device features updated in the data base 
    # handle the subscribe to the home-broker devices
    # for each subscribe callback compare to previous
    # update differences only NO state information
    #previous = None
    #print("mt2", type(previous), type(current))
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
        global topic_to_device_feature
        #print("glob", type(previous), type(current))
        topic_to_device_feature = {}
        unzipped = zlib.decompress(payload)
        current = json.loads(unzipped)
        force_db_check = False
        print("loaded", type(previous), type(current))
        if previous is None:
            previous = copy.deepcopy(current)
            #print("compare_and_update set previous",type(previous), type(current))
            force_db_check = True # first time after starting so we check/update if needed
        #print("check friendly name", type(previous), type(current),type(None))
        for friendly_name in (current.keys()):
            print("compare_and_update[%s]" % (friendly_name))
            if friendly_name in previous:  # exists
                #print(friendly_name, type(previous), type(current))
                #print("prev", previous[friendly_name] )
                if (current[friendly_name]['description'] != previous[friendly_name]['description'] or
                   current[friendly_name]['date']         != previous[friendly_name]['date'] or
                   current[friendly_name]['source']       != previous[friendly_name]['source'] or
                   force_db_check):
                    self.update_mqtt_device(friendly_name);
                if self.FEATURES in current[friendly_name]:  # has features check for changes
                    for feature in (current[friendly_name][self.FEATURES].keys()):  # each feature
                        #print("\t", feature)
                        current_feature =   copy.deepcopy(current[friendly_name][self.FEATURES][feature])
                        previous_feature =  copy.deepcopy(previous[friendly_name][self.FEATURES][feature])
                        # print(current_feature)
                        update_needed = False
                        for tag in current_feature.keys():
                            print("feature tag [%s]"% (tag,))
                            if (current_feature[tag] != previous_feature[tag]):
                                update_needed = True
                                break
                        if update_needed == True or force_db_check:
                            self.update_feature(friendly_name, feature, current_feature)
            else:
                self.insert_device(friendly_name)
        self.db.commit()

    def insert_device(self,friendly_name):
        global current
        print("---------------insert_device--------------------")
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
                cur.execute('''insert into mqtt_devices (friendly_name, description, source, last_mqtt_time
)"
                        values (?,?,?,?)''',
                friendly_name,
                feature,
                f[friendly_name]['description'], 
                f[friendly_name]['date'],         
                f[friendly_name]['source'],
                self.now)
                cur.close()
                self.db.commit()
       
    def update_mqtt_device(self,friendly_name):
        global current
        desc = current[friendly_name]['description'] 
        self.date = int(current[friendly_name]['date'])        
        src = current[friendly_name]['source'] 
        print("update_mqtt_device[%s][%s][%s]\n\t[%s]" % (friendly_name, time.ctime(self.date), src, desc,))
        cur = self.db.cursor()
        cur.execute('''INSERT INTO mqtt_devices(friendly_name, description, source, last_mqtt_time) values (?,?,?,?)
              ON CONFLICT(friendly_name) DO UPDATE SET description=?, source =?, last_mqtt_time=?''',
                    (friendly_name, desc, src, self.date, desc, src, self.date,))
        cur.close()
        

    def update_feature(self, friendly_name, feature, current_feature):
        global topic_to_device_feature
        access = current_feature["access"]
        description = current_feature["description"]
        topic = current_feature["topic"]
        type = current_feature["type"]
        false_value = current_feature["false_value"]
        true_value = current_feature["true_value"]
        
        print("update_feature[%s][%s][%s][%s][%s]\n\t[%s]\n\t[%s]\n\t[%s][%s]" % 
              (friendly_name, feature, access, type, self.date, description, topic, false_value, false_value,))
        if (current_feature["access"] == "sub"):  # we publish using these
            cur = self.db.cursor()
            cur.execute('''INSERT INTO publish_feature(friendly_name, feature, topic, type, description, true_value, false_value, last_mqtt_time) values (?,?,?,?,?,?,?,?)
                  ON CONFLICT(friendly_name,feature) DO UPDATE SET topic =?, description=?, true_value=?, false_value=?, last_mqtt_time=?''',
                        (friendly_name,
                        feature,
                        topic,
                        type,
                        description,
                        true_value,
                        false_value,
                        last_mqtt_time,
                        topic,
                        type,
                        description,
                        true_value,
                        false_value,
                        last_mqtt_time,))
            cur.close()
        elif (current_feature["access"] == "pub"):  # we subscribed to this
            #
            # we build the subscribed topic_to_device_feature dictionary
            # used when subscribe callbacks arrive
            # print(type(current_feature))
            #
            # topic_to_device_feature dictionary is to speed up the callbacks from subscribes
            # 
            topics = []
           
                print("topic_to_device_feature",current_feature["topic"])
                if current_feature["topic"] in topic_to_device_feature: 
                    print("topic_to_device_feature >> adding more",current_feature["topic"], topic_to_device_feature[current_feature["topic"]])
                    topics = topic_to_device_feature[current_feature["topic"]]
                topics.append([friendly_name, feature])
                topic_to_device_feature[current_feature["topic"]] = topics
            #print("update_feature", friendly_name, current_feature)
            cur = self.db.cursor()
            cur.execute('''INSERT INTO subscribed_features(friendly_name, feature, topic, type, description, true_value, false_value, last_mqtt_time) values (?,?,?,?,?,?,?,?)
                  ON CONFLICT(friendly_name,feature) DO UPDATE SET topic =?, description=?, true_value=?, false_value=?, last_mqtt_time=?''',
                        (friendly_name,
                        feature,
                        topic,
                        type,
                        description,
                        true_value,
                        false_value,
                        last_mqtt_time,
                        topic,
                        type,
                        description,
                        true_value,
                        false_value,
                        last_mqtt_time,))
            cur.close()
        else:
            Print("update_feature invalid access[%s]" % (current_feature["access"]))

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
    import pprint
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
    
    print("\n\n test 1  check if equal")
    previous = json.loads(json_1)
    check.compare_and_update(payload_1) 
    
    print("\n\n test 2  check differences")
    
    # test 2 check when differences      
    previous  = json.loads(json_2)
    check.compare_and_update(payload_1)  
    
    print("\n\n test 3  check against database")
    # test 3 check when None previous, starting up for example
    # need to check against database, slower  
    previous = None    
    check.compare_and_update(payload_1)  

    pprint.pprint(topic_to_device_feature)
                    
