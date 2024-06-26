# MIT Licence 
import database
import json
from message import publish_single
import const
from mqtt_hello import hello_refresh_request


'''The access property is a 3-bit bitmask.

Bit 1: The property can be found in the published state of this device.
Bit 2: The property can be set with a /set command
Bit 3: The property can be retrieved with a /get command (when this bit is true, bit 1 will also be true)
'''
#
# conditional print
import os 
my_name = os.path.basename(__file__).split(".")[0]
raw_print = print # copy print
def print(*args, **kwargs): # replace print
    #return
    raw_print("["+my_name+"]", *args, **kwargs) # the copied real print
#
#
def load_IP_device(db, address, payload):
    print("processing %s" % (address,))
    source = "IP"
    change_record_count = 0
    # print("Loading device descriptor:\n```\n%s\n```" % payload) 
    try:
        device =json.loads(payload)
    except:
        print("json.loads failed")
        print(payload)
        return
    try:
        name = device["name"]
        description = device["desc"]
        features = device["features"]
        print("name[%s] desc[%s]" % (name, description))
        exists = db.upsert_device(description, name, source)
        if not exists:
            change_record_count += 1
    except Exception:
        print("upsert_device failed [%s]" % (Exception,))
    else:
        for f in features:
            try:
                type = f["type"]
                property = f["property"]
                access = f["mqtt"]
                print("feature: "+property)
            except:
                print("feature failed for[%s]" % (name,))
            else:
                topic = f["topic"] if "topic" in f else f["pub_topic"] if "pub_topic" in f else None
                feature_description = f["desc"] if "desc" in f else None
                exists = db.upsert_feature(  name, 
                                    property,  
                                    feature_description,
                                    type,
                                    access,
                                    topic,
                                    f["payload_on"]  if "payload_on"  in f else None,
                                    f["payload_off"] if "payload_off" in f else None,
                                )
                if not exists:
                    change_record_count += 1
        if change_record_count > 0:
            publish_single(hello_refresh_request, "load_IP_device") 

# this is a load of some test data from micropython devices 
if __name__ == "__main__":
    valve_payload = '''
{
"name": "main_valve",
"desc": "motor valve controller, with feedback",
"features":
[
{"mqtt": "sub", "property": "toggle", "desc": "supports on and off", "type": "binary", "payload_off": "off", "payload_on": "on", "topic": "home/main_valve/toggle"}
,{"mqtt": "pub", "property": "state", "desc": "current state on, off or unknown", "type": "binary", "payload_on": "on", "payload_off": "off", "payload_unknown": "unknown", "topic": "home/main_valve/state"}
,{"mqtt": "pub", "property": "anomaly", "desc": "Text payload describing problems or issues", "type": "text", "topic": "home/main_valve/anomaly"}   
]
}
'''
   #  topic, payload = _example_home_broker_publish()
    device =json.loads(valve_payload)
    print("device [%s]" % (device,))
    load_IP_device(valve_payload)

    door_bell_payload = '''
{
"name": "door_bell",
"desc": "Four different chimes",
"features":
[
{"mqtt": "sub", "property": "ding_ding", "desc": "Ding ding chime", "type": "momentary", "payload_on": "pressed", "topic": "home/door_bell/ding_ding"}
,{"mqtt": "sub", "property": "ding_dong", "desc": "Ding dong chime", "type": "momentary", "payload_on": "pressed", "topic": "home/door_bell/ding_dong"}
,{"mqtt": "sub", "property": "westminster_abby", "desc": "Westminster abby chime", "type": "momentary", "payload_on": "pressed", "topic": "home/door_bell/westminster_abby"}
,{"mqtt": "sub", "property": "three_chimes", "desc": "westminster_abby, ding ding and ding dong chimes", "type": "momentary", "payload_on": "pressed", "topic": "home/door_bell/three_chimes"}
,{"mqtt": "pub", "property": "button", "desc": "simple momentary event", "type": "momentary", "payload_on": "pressed", "topic": "home/door_bell/button"}
]
}'''
    device =json.loads(door_bell_payload)
    print("device [%s]" % (device,))
    load_IP_device(door_bell_payload)
