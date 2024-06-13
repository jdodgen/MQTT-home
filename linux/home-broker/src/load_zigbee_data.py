import message 
import database
import json
import time
import queue
import const
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

class ZigbeeDeviceRefresher():
    def __init__(self):
        self.db = database.database()
        q = queue.Queue()  
        self.msg = message.message(q, my_parent=my_name)
        self.msg.client.subscribe(const.zigbee2mqtt_bridge_devices, 0)

        while True:
            try:
                item = q.get(timeout=20)
            except queue.Empty:
                print("ZigbeeDeviceRefresher empty sleeping")
                time.sleep(1)
                continue
            if item is None:
                print("ZigbeeDeviceRefresher: no reply from ", self.topic)
                break
            print("ZigbeeDeviceRefresher item[0] [%s]" % (item[0],))
            if item[0] == "callback":
                if item[1] == const.zigbee2mqtt_bridge_devices: # reply topic
                    load_database_from_zigbee(item[2])
                    break

def load_database_from_zigbee(zigbee2mqtt_devices):
    #print("\n\n",zigbee2mqtt_devices,"\n\n")
    db = database.database()

    db.delete_all_zb_devices()
    devices =json.loads(zigbee2mqtt_devices)
    #print("\n\n",devices,"\n\n")
    for d in devices:
        #print(d.keys())
        device_type=d["type"]
        # print("device_type[%s]" % (device_type,))
        #print("device_type[%s]" % (device_type,))
        if device_type == "Coordinator":
            continue  # ignore for now
        #print("we care about [%s]" % device_type)
        definition= d["definition"]
        address=d["ieee_address"]
        name = d["friendly_name"]
        if not name:
            continue
        #print("definition[%s]" % type(definition))
        if definition == "None":
            continue
        #print("definition", definition)
        description = definition["description"]   
        print("description[%s]  ieee[%s] friendly[%s]" % (description, address, name))
        rc = db.upsert_device(description, name, "ZB")
        #print("load_database_from_zigbee rc", rc)
        exposes = definition["exposes"]
        
        for e in exposes:
            #print("exposes:", e) 
            if 'features' in e:
                e = e['features'][0] # not sure why 'features' wraps this, so process as normal
            access = e["access"]
            if e.get('description') == None:
                desc=None
            else:
                desc = e["description"]
                del e["description"]
            property = e["property"]
            type= e["type"]
            #  now create the topics
            true_value = None
            false_value = None
       
            if type == 'binary':
                true_value = '{"%s": "%s"}' % (property, e["value_on"])
                false_value = '{"%s": "%s"}' % (property, e["value_off"])
            elif type == 'enum':
                true_value = '{"%s": "%s"}' % (property, "on")
                false_value = '{"%s": "%s"}' % (property, "off")
            elif type == 'numeric':
                true_value = '{"%s": "%s"}' % (property, "number")
                false_value = None

            can_published, can_set, can_get = parse_access_flags(access)
            print("name[%s] property[%s] access[%s] published[%s] set[%s] get[%s]" % (name, property, access, can_published, can_set, can_get,))
            if can_set:
                topic = "zigbee2mqtt/%s/set" %  (name)
                pubsub = "sub"
                db.upsert_feature(name, 
                                property,  
                                desc,
                                type,
                                pubsub,
                                topic,
                                true_value,
                                false_value,
                                )
                #print("did set")
            if can_get:
                topic = "zigbee2mqtt/%s/get" %  (name)
                pubsub = "sub"
                db.upsert_feature(name, 
                                property,  
                                desc,
                                type,
                                pubsub,
                                topic,
                                true_value,
                                false_value,
                                )
                #print("did get")
            if can_published:
                topic = "zigbee2mqtt/%s" % name
                pubsub = "pub"    
                db.upsert_feature(name, 
                                property,  
                                desc,
                                type,
                                pubsub,
                                topic,
                                true_value,
                                false_value,
                                )
                #print("did publish")

def parse_access_flags(access):
    published = True if (access & 1) else False
    set         = True if (access & 2) else False
    get         = True if (access & 4) else False
    return (published, set, get)

if __name__ == "__main__":
    d=ZigbeeDeviceRefresher()
    time.sleep(10)
    #import sample_zigbee2mqtt_bridge_devices
    #load_database_from_zigbee(sample_zigbee2mqtt_bridge_devices.sample_zigbee2mqtt_bridge_devices)

