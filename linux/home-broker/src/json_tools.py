import json
import const
import database
import time
#
# conditional print
import os 
my_name = os.path.basename(__file__).split(".")[0]
xprint = print # copy print
def print(*args, **kwargs): # replace print
    return
    xprint("["+my_name+"]", *args, **kwargs) # the copied real print
#
#
"""
Generic: types like numeric and binary
Specific: represents a specific capability of a device like a light or switch.

Both types will always have a type property.  
The generic types (except composite) will always have an access property (3 bits)
and an optional description property.
 All generic types will always have a name property 
 indicating the context and label property containing the name 
 of the capability in the correct case and without using the underscore 
 separator (e.g. Device temperature, VOC, Power outage count). 
 
 All generic  types will always have a property type indicating where the value is exposed 
 on, usually this is equal to the name but in case when the endpoint is defined 
 it is name_endpoint. The specific and the generic composite type will always 
 have a features property, this is an array containing the generic exposes types.
   Optionally both types can have a property endpoint, indicating the device exposes
     this capability on a specific endpoint.
"""

# binary   json   value_on value_off value_toggle
# numeric {"unit": "lqi", "value_max": 255, "value_min": 0}]
# this is to get all the "get, set, status" mqtt stuff

def j2d_manual_device(j):
    stuff = json.loads(j)
    if "set" not in stuff.keys(): stuff["set"] = None
    if "get" not in stuff.keys(): stuff["get"] = None
    if "on" not in stuff.keys(): stuff["on"] = None
    if "off" not in stuff.keys(): stuff["off"] = None
    if "status" not in stuff.keys(): stuff["status"] = None  
    print("set[%s] get[%s] on[%s] off[%s] status[%s]" % (stuff["set"], stuff["get"], stuff["on"], stuff["off"], stuff["status"]))
    return stuff

def d2j_manual_device(d):
    if "set" not in d.keys(): d["set"] = None
    if "get" not in d.keys(): d["get"] = None
    if "on" not in d.keys(): d["on"] = None
    if "off" not in d.keys(): d["off"] = None
    if "status" not in d.keys(): d["status"] = None
    deletes=[]
    for key in d:   # clean out future json
        if key not in  ("set", "get", "on", "off"):
            deletes.append(key)
    for key in deletes:
        del d[key]
    return json.dumps(d)

def j2d_zigbee_device(name,j):
    stuff = json.loads(j)
    if "set" not in stuff.keys(): stuff["set"] = None
    if "get" not in stuff.keys(): stuff["get"] = None
    if "on" not in stuff.keys(): stuff["on"] = None
    if "off" not in stuff.keys(): stuff["off"] = None
    if "status" not in stuff.keys(): stuff["status"] = None  
    print("set[%s] get[%s] on[%s] off[%s] status[%s]" % (stuff["set"], stuff["get"], stuff["on"], stuff["off"], stuff["status"]))
    return stuff

if __name__ == "__main__":
   
    y = '{"set": "turn_me_on", "on":  "ON", "off": "OFF", "status": "what_am_I"}'
    dict = j2d_manual_device(y)
    dict["foobar"] = "wtf"
    dict["xxxx"] = "xxxwtf"
    print(dict)  
    j = d2j_manual_device(dict)
    print(j)
