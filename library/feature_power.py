# MIT licence Copyright Jim dodgen 2024

xprint = print # copy print
def print(*args, **kwargs): # replace print
    return # comment/uncomment to turn print on off
    xprint("[feature_power]", *args, **kwargs) # the copied real print    

# modify here
base_topic = "home"
tail_topic = "power"

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
        "desc": "Monitoring power from utility",
        "type": "binary",
        "payload_off": "off", 
        "payload_on": "on", 
        "topic": base_topic+"/"+name+"/"+tail_topic  
        }

class feature:
    def __init__(self, name, subscribe=False, publish=False):
        self.cooked = feat(name, subscribe=subscribe, publish=publish)
        print(self.cooked)

    def cooked(self):
        return self.cooked
    
    def topic(self):
        return self.cooked["topic"]   # publisher "sets" this subscriber subscribes to a published topic
    
    def payload_on(self):
        return self.cooked["payload_on"] 
    
    def payload_off(self):
        return self.cooked["payload_off"] 

# unit tests
# if __name__ == "__main__":
#     alert = feature_alert("Alarm_button")
#     json = alert.feature_json()
#     print(json)
#     on = alert.payload_on()
#     off = alert.payload_off()
 
