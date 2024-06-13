import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
import sys
import socket
import const
import time
#
# conditional print
import os 
my_name = os.path.basename(__file__).split(".")[0]
parent = None
xprint = print # copy print
def print(*args, **kwargs): # replace print
    #return
    tag = "["+my_name+"("+parent+")]" if parent else my_name 
    xprint("["+tag+"]", *args, **kwargs) # the copied real print
#
#
mqtt_broker = "home-broker.local"
#
#
class client_instance():
    def __init__(self):
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2) #, our_ip_address())
        ip = mqtt_broker
        for x in range(10):
            try:
                print("message: attempting mqtt connection [%s}" % (ip,))
                self.client.connect(ip, keepalive=120) 
                break
            except:
                print("message: MQTT could not connect [%s]" % (ip,))
                time.sleep(10)

            # the loop will try later
        #self.client.on_message=self.on_message
        
        self.client.on_message =   self.on_message  # this one uses the queue
        self.client.on_connect =   self.on_connect
        self.client.on_publish =   self.on_publish
        self.client.on_subscribe = self.on_subscribe

        self.client.loop_start()
        self.last_subscribe = ""
        self.last_subscribe_time = 0
     
    def connect_fail_callback(client, userdata):
        print("connect failed")
        
    def on_connect(self, client, userdata, flags, reason_code, properties):
        print("on_connect client[%s] reason_code[%s]" % (client, reason_code,))
    
    def on_message(self, client, userdata, message):
        payload_size = sys.getsizeof(message.payload)
        print("message.on_message: callback client[%s] topic[%s] payload size[%s]" % (client, message.topic, payload_size))

    def on_publish(self, client, userdata, mid, reason_code, properties):
        # reason_code and properties will only be present in MQTTv5. It's always unset in MQTTv3
        try:
            userdata.remove(mid)
        except:
            xprint("\non_publish() is called with a mid not present in unacked_publish")
            xprint("This is due to an unavoidable race-condition:")
            xprint("* publish() return the mid of the message sent.")
            xprint("* mid from publish() is added to unacked_publish by the main thread")
            xprint("* on_publish() is called by the loop_start thread")
            xprint("While unlikely (because on_publish() will be called after a network round-trip),")
            xprint(" this is a race-condition that COULD happen")
            xprint("")
            xprint("The best solution to avoid race-condition is using the msg_info from publish()")
            xprint("We could also try using a list of acknowledged mid rather than removing from pending list,")
            xprint("but remember that mid could be re-used !\n")

    def on_subscribe(self, client, userdata, mid, reason_code_list, properties):
        # Since we subscribed only for a single channel, reason_code_list contains
        # a single entry
        if reason_code_list[0].is_failure:
            print(f"Broker rejected you subscription: {reason_code_list[0]}")
        else:
            print(f"Broker granted the following QoS: {reason_code_list[0].value}")

    def publish(self, topic, payload, retain=False):
        ptype=type(payload)
        payload_size = sys.getsizeof(payload)
        print("message.publish: topic [%s] payload [%s] payload type[%s]" % (topic, payload_size, ptype))
        if ptype is str:
            #print(""message.publish: payload is string")
            rc = self.client.publish(topic, bytes(payload, 'utf-8'))
        else:
            rc = self.client.publish(topic, payload)
    
    def subscribe(self,topic):
         t = time.time()
         self.client.subscribe(topic)
         print("message.subscribe[%s]" % (topic,))
         return True

### test area ###
if __name__ == "__main__":
    msg = client_instance()
    # msg.subscribe("mp_test/sub")
    while True:
        msg.publish("mp_test/pub","nothing")
        msg.subscribe("mp_test/sub")
        time.sleep(30)

