# MIT licence Copyright Jim dodgen 2024
# simple on/off feature

xprint = print # copy print
def print(*args, **kwargs): # replace print
    return # comment/uncomment to turn print on off
    xprint("[feature_button]", *args, **kwargs) # the copied real print

base_topic = "home"

tail_topic = "button"

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
        "desc": "simple momentary event",
        "type": "momentary",
        "payload_on": "pressed",
        "topic": base_topic+"/"+name+"/"+tail_topic
        }

class feature:
    def __init__(self, name, subscribe=False, publish=False):
        self.cooked = feat(name, subscribe=subscribe, publish=publish)
        print(self.cooked)

    def get(self):
        return self.cooked

    def topic(self):
        return self.cooked["topic"]   # publisher "sets" this subscriber subscribes to a published topic

    def payload_on(self):
        return self.cooked["payload_on"]


# # unit tests
# if __name__ == "__main__":
#     butt = feature_button("Alarm_button")
#     json = butt.feature_json()
#     print(json)
#     topic = butt.publish_topic()
#     print(topic)
#     off = butt.payload_off()
#     on = butt.payload_on()
