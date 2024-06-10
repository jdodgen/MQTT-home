import json

xprint = print # copy print
def print(*args, **kwargs): # replace print
    #return # comment/uncomment to turn print on off
    # do whatever you want to do
    #xprint('statement before print')
    xprint("[feature_state]", *args, **kwargs) # the copied real print    

base_topic = "home"
tail_topic = "state"

def feat(name,  subscribe=False, publish=False):
    if subscribe is True:
        pubsub="sub"
    elif publish is True:
        pubsub="pub"
    else:
        pubsub="unknown"
    return { 
        "mqtt": pubsub,   
        "property": tail_topic,
        "desc": "current state on, off or unknown",
        "type": "binary",
        "payload_on": "on", 
        "payload_off": "off", 
        "payload_unknown": "unknown", 
        "topic": base_topic+"/"+name+"/"+tail_topic  
        }

class feature:
    def __init__(self, name, subscribe=False, publish=False):
        self.cooked = feat(name, subscribe=subscribe, publish=publish)
        print(self.cooked)

    def feature_json(self):
        config_json = json.dumps(self.cooked)
        return config_json
    
    def topic(self):
        return self.cooked["topic"]   # publisher "sets" this subscriber subscribes to a published topic
    
    def payload_on(self):
        return self.cooked["payload_on"] 
    
    def payload_off(self):
        return self.cooked["payload_off"] 
    
    def payload_unknown(self):
        return self.cooked["payload_unknown"] 

# # unit tests
# if __name__ == "__main__":
#     feat = feature("water_main")
#     json = feat.feature_json()
#     print(json)
#     on = feat.payload_on()
#     off = feat.payload_off()
#     print("payload_on [%s], payload_off[%s]" % (on, off,))
 
