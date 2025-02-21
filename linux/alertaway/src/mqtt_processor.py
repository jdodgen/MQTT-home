# Copyright Jim Dodgen 2024 MIT licence
# this is an interface between home-broker/mqtt and alertaway
# It maintains the device database tables configuration
# as well as handling the messages from subscribes
# updating the device database tables with current values
# most work is done using the in-memory structure from home-broker to
# reduce the activity on the database.
#
import os

if os.name != 'nt':
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
    submsg = subscribe_messages(db)
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
                submsg.update(topic,payload)

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
                            print("feature[%s]"% (tag,))
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
        print("insert a new device[%s]" % (friendly_name))
        self.update_mqtt_device(friendly_name)
        if self.FEATURES in current[friendly_name]:  # has features check for changes
            for feature in (current[friendly_name][self.FEATURES].keys()):  # each feature
                current_feature = copy.deepcopy(current[friendly_name][self.FEATURES][feature])
                self.update_feature(friendly_name, feature, current_feature)
       
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
class subscribe_messages():
    def __init__(self, db):
        self.db = db	
    def update(self, topic, payload_in):
        global topic_to_device_feature
        now = str(int(time.time())) # standard unix time in a string
        tod_features = topic_to_device_feature[topic]
        print("features for [%s]" % (topic))
        pprint.pp(tod_features)
        try:
            payload = json.loads(payload_in)
        except:  # not json, simple string
            print("simple [%s][%s]" % (topic, payload_in))
            value=payload_in
            for f in tod_features: 
                friendly_name = f[0]
                feat = f[1] 
                print("found a match value[%s] to be updated to friendly_name[%s] feature[%s]" %
                        (value, friendly_name, feat))
                cur = self.db.cursor()
                cur.execute('''update subscribed_features set current_value=?,last_report_time=?
                            where friendly_name=? and feature=?''', (value, now, friendly_name, feat))
                cur.close()
        else: # process json, can have multiple values affecting both subscribes as well as status from state changes
            print("json payload [%s]" % (topic))
            pprint.pp(payload)
            for payload_feature in payload: 
                value=payload[payload_feature]
                if (payload_feature[:5] == "state"): # this can  be the result of a publish 
                    print("found a [%s]=[%s]" % (payload_feature, value))
                    cur = self.db.cursor()
                    cur.execute('''update publish_feature set current_value=?
                        where friendly_name=? and feature=?''', (value, friendly_name, feat))
                    cur.close()
                print("payload topic[%s]feat[%s]value[%s]" % (topic, payload_feature, value)) 
                for topic_to_device_feat in tod_features: 
                    friendly_name = topic_to_device_feat[0]
                    feat = topic_to_device_feat[1]
                    if (feat == payload_feature):
                        value=payload[feat]
                        print("found a match value[%s] to be updated to friendly_name[%s] feature[%s]" %
                            (value, friendly_name, feat))
                        cur = self.db.cursor()
                        cur.execute('''update subscribed_features set current_value=?,last_report_time=?
                            where friendly_name=? and feature=?''', (value, now, friendly_name, feat))
                        cur.close()
        self.db.commit()

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
# test area, leave test code behind for future  use  
#
if __name__ == "__main__":
    print("\n\n------Testing------\n")
    db = sqlite3.connect("devices.db", timeout=const.db_timeout)
    rebuild = True
    if rebuild == True:
        with open("test_json.js", 'r') as file:
            json_1 = file.read()
        # sample payload 
        payload_1 = zlib.compress(bytes(json_1,'utf-8'))
        check = check_and_refresh_devices(db)
        check.compare_and_update(payload_1)
    sm=subscribe_messages(db)
    print("Testing update")
    sm.update("home/main_valve/state","on")
    sm.update("home/main_valve/state","on")
    sm.update("zigbee2mqtt/corded_leak","{\"linkquality\": \"98\", \"water_leak\": \"True\", \"battery_low\": \"False\"}")
    sm.update("home/main_valve/state","on")
   
#     exit()

#     # more tests
#      #mqtt_task()
#     db = sqlite3.connect("test.db", timeout=const.db_timeout)
#     check = check_and_refresh_devices(db)	
    
#     print(">>>>>>%s<<<<<<" % (json_1))
#     '''
#     print("\n\n test 1  check if equal")
#     previous = json.loads(json_1)
#     check.compare_and_update(payload_1) 
    
#     print("\n\n test 2  check differences")
    
#     # test 2 check when differences      
#     previous  = json.loads(json_2)
#     check.compare_and_update(payload_1)  
#   '''
#     print("\n\n test 3 startup no previous so check against database")
#     # test 3 check when None previous, starting up for example
#     # need to check against database, slower  
#     previous = None    
#     check.compare_and_update(payload_1)  
#     print("\ntopic_to_device_feature\n")
#     pprint.pprint(topic_to_device_feature)
#     ms = manage_subscriptions(db,None)
#     ms.subscribe()