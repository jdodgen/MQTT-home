'''
MIT License

Copyright (c) 2023,2024 Jim Dodgen

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''

import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
import paho.mqtt.subscribe as subscribe
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
    return
    tag = "["+my_name+"("+parent+")]" if parent else my_name 
    xprint("["+tag+"]", *args, **kwargs) # the copied real print
#
#
#my_parent = "xxx"
#print("hello [%s]" % ("x",))

def our_ip_address():
    if const.mqtt_broker:
        ip = const.mqtt_broker
    else:
        import fcntl
        import struct
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("192.168.253.253", 50000))
        ip = s.getsockname()[0]
    print("ip address",ip)
    return ip

    # hostname = socket.gethostname()
    # print("my host name [%s]" % (hostname,))
    # ip_address = socket.gethostbyname(hostname)
    # print("broker IP address [%s]" % (ip_address,))
    # return ip_address

class message():
    def __init__(self, queue=None, my_parent=None):
        global parent
        parent = my_parent
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.q = queue
        self.unacked_publish = set()
        self.client.user_data_set(self.unacked_publish)
        ip = our_ip_address()
        for x in range(10):
            try:
                print("attempting mqtt connection ")
                self.client.connect(ip, keepalive=const.mqtt_keepalive) 
                break
            except:
                print("MQTT could not connect [%s]" % (ip,))
                time.sleep(10)

            # the connect will try later
        #self.client.on_message=self.on_message
        
        self.client.on_message =   self.on_message  # this one uses the queue
        self.client.on_connect =   self.on_connect
        self.client.on_publish =   self.on_publish
        self.client.on_subscribe = self.on_subscribe

        self.client.loop_start()
        self.last_subscribe = ""
        self.last_subscribe_time = 0
    
    ### def on_publish(self,client,userdata,result):             #create function for callback
    def xon_publish(self, client, userdata, mid, reason_codes, properties):
        print("on_publish: mid[%s]" % (mid,))

    def connect_fail_callback(client, userdata):
        pass

    def on_connect(self, client, userdata, flags, reason_code, properties):
    # def on_connect(self, client, userdata, flags, rc ):
        """Subscribe to state command on connect (or reconnect)."""
        #print("message: client[%s] connected" % client)
        #when reconnect existing subscribes must be re-subscribed
        print("on_connect reason_code[%s]" % (reason_code,))
        if self.q != None:
             self.q.put(("connected",None,None))
    
    def on_message(self, client, userdata, message):
        payload_size = sys.getsizeof(message.payload)
        print("on_message client[%s] topic[%s] payload size[%s]" % (client, message.topic, payload_size)) 
        # all messages are forwarded via the passed in queue
        self.q.put(("callback", message.topic, message.payload))

    def on_publish(self, client, userdata, mid, reason_code, properties):
        # reason_code and properties will only be present in MQTTv5. It's always unset in MQTTv3
        try:
            if mid:
                userdata.remove(mid)
        except:
            print("on_publish() is called with a mid not present in unacked_publish")
            print("This is due to an unavoidable race-condition:")
            print("* publish() return the mid of the message sent.")
            print("* mid from publish() is added to unacked_publish by the main thread")
            print("* on_publish() is called by the loop_start thread")
            print("While unlikely (because on_publish() will be called after a network round-trip),")
            print(" this is a race-condition that COULD happen")
            print("")
            print("The best solution to avoid race-condition is using the msg_info from publish()")
            print("We could also try using a list of acknowledged mid rather than removing from pending list,")
            print("but remember that mid could be re-used !")

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
        print("publish: topic [%s] payload [%s] payload type[%s]" % (topic, payload_size, ptype))
        if ptype is str:
            #print(""message.publish: payload is string")
            rc = self.client.publish(topic, bytes(payload, 'utf-8'), retain=retain)
        else:
            rc = self.client.publish(topic, payload, retain=retain)
        self.unacked_publish.add(rc.mid)
        #print("message.publish wait_for_publish")
        #rc.wait_for_publish() 
        #print("message.publish return [%s]" % rc.is_published())
    
    def subscribe(self,topic):
         t = time.time()
         #if topic == self.last_subscribe and self.last_subscribe_time < t + 2:
              #print("message.subscribe duplicate, ignored", topic)
              #return False
         self.last_subscribe = topic
         self.last_subscribe_time = t
         self.client.subscribe(topic)
         print("subscribe[%s]" % (topic,))
         return True
         
    def cook(self, s):
         return bytes(s, 'utf-8')
    
def publish_single(topic, payload, my_parent=None):
    global parent
    parent = my_parent
    print("publish_single: topic[%s] payload[%s] broker[%s]" % 
          (topic, payload, our_ip_address(),))
    rc = publish.single(topic, payload, hostname=our_ip_address()) 
    print("publish_single returned[%s]" % rc)

def resubscribe(client, userdata, message):
    xprint("resubscribe for %s" % (message.topic,))
    client.unsubscribe(message.topic)
    client.subscribe(message.topic)

def simple_subscribe(topic, my_parent=None):
    global parent
    parent = my_parent
    print("simple_subscribe: topic[%s]  broker[%s]" % 
          (topic, our_ip_address(),))
    rc = subscribe.callback(resubscribe, topic, hostname=our_ip_address()) 
    print("simple_subscribe returned[%s]" % rc)
    

### test area ###
if __name__ == "__main__":
    import queue
    q = queue.Queue() 
    msg = message(q)

    msg.publish("message_unit_test/demo_wall/set", '{"state": "on"}')
    msg.publish("message_unit_test/jake/set", '{"state": "on"}')
    msg.subscribe("message_unit_test/joe/")
    msg.subscribe("message_unit_test/jake/#")
    msg.subscribe("message_unit_test/motion/#")
    msg.subscribe("message_unit_test/demo_wall/#")
    time.sleep(2) # pretter output
    while True:
        msg = q.get()
        print("message_unit_test: q.get()", msg)

