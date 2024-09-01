# Copyright Jim Dodgen 2024 MIT licence
# this is an interface between home-broker/mqtt and alertaway
# It maintains the device database tables configuration
# as well as handling the messages from subscribes
# and updating the device database tables current values
#
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
import pprint

current = None
previous = None
#print("None", type(previous), type(current))
topic_to_device_feature = None

# conditional print
xprint = print # copy print
def print(*args, **kwargs): # replace print
    # return
    xprint("[mqtt_processor]", *args, **kwargs) # the copied real print 

def mqtt_task():
    global previous
    #print("mt", type(previous), type(current))
    # keep device features updated in the database 
    # handle the subscribe to the home-broker devices
    # for each subscribe callback compare to previous
    # update differences only NO state information
    #previous = None
    #print("mt2", type(previous), type(current))
    db = sqlite3.connect(const.db_name, timeout=const.db_timeout)
    q = queue.Queue() # callbacks are sent here
    msg = message.message(queue=q, client_id="alertaway") # MQTT connection tool
    check = check_and_refresh_devices(db)	
    updates = device_state(db)
    ms = manage_subscriptions(db, msg)
    msg.subscribe(const.home_MQTT_devices)
    while True:
        (action, topic, payload) = q.get()
        if (action == "callback"):
            print("callback",type(topic), type(payload))
            if (topic == const.home_MQTT_devices):
                check.compare_and_update(payload)
                ms.subscribe()
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
        # consider moving current and previous here 

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
            else: # we picked up a new one
                self.insert_device(friendly_name)
        self.db.commit()

    def insert_device(self,friendly_name):
        global current
        print("insert a new device[%s]" % (frendly_name))
        self.update_mqtt_device(riendly_name)
        if self.FEATURES in current[friendly_name]:  # has features check for changes
            for feature in (current[friendly_name][self.FEATURES].keys()):  # each feature
                current_feature = copy.deepcopy(current[friendly_name][self.FEATURES][feature])
                self.update_feature(friendly_name, feature, current_feature):
       
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
            cur.execute('''INSERT INTO publish_feature
                (friendly_name, feature, topic, type, description, true_value_or_data, false_value, last_mqtt_time) 
                values (?,?,?,?,?,?,?,?)
                ON CONFLICT(friendly_name,feature) DO UPDATE 
                SET topic=?, type=?, description=?, true_value_or_data=?, false_value=?, last_mqtt_time=?''',
                        (friendly_name,
                        feature,
                        topic,
                        type,
                        description,
                        true_value,
                        false_value,
                        self.date,
                        topic,
                        type,
                        description,
                        true_value,
                        false_value,
                        self.date,))
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
            cur.execute('''INSERT INTO subscribed_features(friendly_name, feature, topic, type, description, true_value_or_data, false_value, last_mqtt_time) values (?,?,?,?,?,?,?,?)
                  ON CONFLICT(friendly_name,feature) DO UPDATE 
                        SET topic =?, type=?, description=?, true_value_or_data=?, false_value=?, last_mqtt_time=?''',
                        (friendly_name,
                        feature,
                        topic,
                        type,
                        description,
                        true_value,
                        false_value,
                        self.date,
                        topic,
                        type,
                        description,
                        true_value,
                        false_value,
                        self.date,))
            cur.close()
        else:
            print("update_feature invalid access[%s] only pub and sub currently" % (current_feature["access"]))

# this handles the callbacks from subscribes 
# the topic is looked up in  current_feature =   copy.deepcopy(current[friendly_name][self.FEATURES][feature]) dictionary 
# and the resultant friendly_name, features will be updated
# if the topic does not exist then the topic is unsubscribed
# just to clean things up
class device_state():
    def __init__(self, db):
        self.db = db	
    def update(self, topic, state):
        global topic_to_device_feature
        print("update from a subscribed [%s][%s]" % (topic, state))
        # using topic_to_device_feature topic gives us a list of friendly_names and features
        # so  ...
        # We need to parse the state and update the correct device/feature
        # This code will need to be updated over time as device stuff changes
        pass

class manage_subscriptions():
    def __init__(self, db, msg):
        self.db = db
        self.msg= msg
    def subscribe(self):
        print(manage_subscriptions)
        if topic_to_device_feature :  # at startup this has not been loaded yet so when loaded it will be called
            sub_topics = []
            for topic in topic_to_device_feature.keys():
                sub_topics.append((topic,1))
            pprint.pprint(sub_topics)
            self.msg.subscribe(sub_topics)
#
#
#
#
# test area        
if __name__ == "__main__":
    import pprint
    mqtt_task()

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
    '''
    print("\n\n test 1  check if equal")
    previous = json.loads(json_1)
    check.compare_and_update(payload_1) 
    
    print("\n\n test 2  check differences")
    
    # test 2 check when differences      
    previous  = json.loads(json_2)
    check.compare_and_update(payload_1)  
  '''
    print("\n\n test 3 startup no previous so check against database")
    # test 3 check when None previous, starting up for example
    # need to check against database, slower  
    previous = None    
    check.compare_and_update(payload_1)  
    print("\ntopic_to_device_feature\n")
    pprint.pprint(topic_to_device_feature)
    ms = manage_subscriptions(db,None)
    ms.subscribe()
                    
