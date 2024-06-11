import json

xprint = print # copy print
def print(*args, **kwargs): # replace print
    return # comment/uncomment to turn print on off
    xprint("[feature_alert]", *args, **kwargs) # the copied real print    

base_topic = "home"
tail_topic = "alert"
def feat(name, subscribe=False, publish=False):
    if subscribe is True:
        pubsub="sub"
    elif publish is True:
        pubsub="pub"
    else:
        pubsub="unknown"
    return { 
        "mqtt": pubsub,   
        "property": "alert",
        "desc": "visual and/or sound emitter",
        "type": "binary",
        "payload_off": "off", 
        "payload_on": "on", 
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
 
