# simple on/off feature 
import json

xprint = print # copy print
def print(*args, **kwargs): # replace print
    # return # comment/uncomment to turn print on off
    xprint("[feature_quad_chimes]", *args, **kwargs) # the copied real print    

base_topic = "home"
tail_topic = "ding_dong"

def feat(name,  subscribe=False, publish=False):
    if subscribe is True:
        pubsub="sub"
    elif publish is True:
        pubsub="pub"
    else:
        pubsub="unknown"
    return { 
        "mqtt": pubsub,   
        "property":tail_topic,
        "desc": "Ding dong chime",
        "type": "momentary",
        "payload_on": "pressed", 
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

# # unit tests
# if __name__ == "__main__":
#      f = feature("foobar",subscribe=True)
#      json = f.feature_json()
#      print(json)
#      topic = f.topic()
#      print(topic)
#      x = f.payload_ding_ding()
#      print(x)
