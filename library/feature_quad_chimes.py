# chimes
# MIT licence Copyright Jim dodgen 2025

xprint = print # copy print
def print(*args, **kwargs): # replace print
    # return # comment/uncomment to turn print on off
    xprint("[feature_quad_chimes]", *args, **kwargs) # the copied real print    

base_topic = "home"
tail_topic = "quad_chimes"

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
        "desc": "HK522 Doorbell IC with West Minister Chime",
        "type": "choices",
        "westminster": "westminster",
        "ding_ding": "ding_ding",
        "ding_dong": "ding_dong",
        "three_chimes": "three_chimes",
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
    
    def payload_westminster(self):
        return self.cooked["westminster"] 
    def payload_ding_ding(self):
        return self.cooked["ding_ding"]
    def payload_ding_dong(self):
        return self.cooked["ding_dong"]
    def payload_three_chimes(self):
        return self.cooked["three_chimes"]

# # unit tests
# if __name__ == "__main__":
#      f = feature("foobar",subscribe=True)
#      json = f.feature_json()
#      print(json)
#      topic = f.topic()
#      print(topic)
#      x = f.payload_ding_ding()
#      print(x)
