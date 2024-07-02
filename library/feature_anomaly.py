# MIT licence Copyright Jim dodgen 2024

xprint = print # copy print
def print(*args, **kwargs): # replace print
    #return # comment/uncomment to turn print on off
    xprint("[feature_anomaly]", *args, **kwargs) # the copied real print    

base_topic = "home"
tail_topic = "anomaly"
def feat(name, subscribe=False, publish=False):
    if subscribe is True:
        pubsub="sub"
    elif publish is True:
        pubsub="pub"
    else:
        pubsub="unknown"
    return { 
        "mqtt": pubsub,   
        "property": tail_topic,
        "desc": "Text payload describing problems or issues",
        "type": "text",
        "topic": base_topic+"/"+name+"/"+tail_topic  
        }

class feature:
    def __init__(self, name, subscribe=False, publish=False):
        self.cooked = feat(name, subscribe=subscribe, publish=publish)
        print(self.cooked)

    def cooked(self):
        return self.cooked
    
    def get(self):
        return self.cooked
    
    def topic(self):
        return self.cooked["topic"]   # publisher "sets" this subscriber subscribes to a published topic
    
 
