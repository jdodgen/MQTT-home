import uuid
import json
#
# conditional print
my_name = "mqtt_hello"
xprint = print # copy print
def print(*args, **kwargs): # replace print
    #return
    xprint("["+my_name+"]", *args, **kwargs) # the copied real print
#
#
hello_tag = "hello"
base_topic = "home"

hello_request_topic =     base_topic+"/home_broker/send_hello"  # I devices subscribe to this.  they publish the /home/xxx/hello payload built here
hello_subscribe_pattern = base_topic+"/+/"+hello_tag # this is a subscribe to capture IP device configs
hello_refresh_request =   base_topic+"/home_broker/refresh"  # when published, causes home-broker to request all devices for stuff

id = hex(uuid.getnode())
print("id[%s]" % (id,))

class hello:
    def __init__(self, name, desc):
        self.name = name
        self.desc= desc
        self.pl = {"name": name, "desc": desc}
        self.list_of_features = []
        # self.pl = head % (json.dump(name), json.dump(desc))

    def add_feature(self, feature):
        self.list_of_features.append(feature)
        #self.pl += feature
        #self.pl += "\n,"

    def payload(self):
        self.pl = {"name": self.name, "desc": self.desc, "features": self.list_of_features}

        return json.dumps(self.pl)

    def topic(self):
        id = hex(uuid.getnode())
        return base_topic+"/"+id[2:]+"/hello"

def raw_send_hello(client, name, desc, *features):
    h = hello(name, desc)
    for f in features:
        h.add_feature(f)
    h.payload()
    topic = h.topic()
    payload = h.payload()
    print("raw_send hello topic[%s] payload\n%s\n" % (topic, payload))
    client.publish(topic, payload)

async def send_hello(client, name, desc, *features):
    h = hello(name, desc)
    for f in features:
        h.add_feature(f)
    h.payload()
    topic = h.topic()
    payload = h.payload()
    print("send_hello:\nTopic: [%s]\nPayload:\n```\n%s\n```\n" % (topic, payload))
    await client.publish(topic, payload)

def request_ip_devices_hello():
   global hello_request_topic
   print("hello_request [%s]" % (hello_request_topic,))
   return hello_request_topic

if __name__ == "__main__":

    raw_send_hello(None,"Alarm_button", "visual and \"audio\" notifier with push button", {"foo1": "x"}, {"foo2":"z"})

    # h = hello(None,"Alarm_button", "visual and audio notifier with push button")
    # h.add_feature(alert.feature_json())
    # h.add_feature(butt.feature_json())
    # print(h.payload())
    # print("hello topic[%s]" % (h.topic(),))

