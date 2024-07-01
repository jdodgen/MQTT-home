# this is an example of a device using MQTT_messages and the related device dictionarys
# Copyright Jim Dodgen 2023 MIT Licence
import universal_mqtt_as
import feature_toggle
import feature_state
import feature_anomaly
import paho.mqtt.client as mqtt
import time
import sys

valve_name = "main_valve"
broker     = "192.168.0.193"

# features 
open_close = feature_toggle.feature(valve_name, publish=True)
state = feature_state.feature(valve_name,     subscribe=True)
problem = feature_anomaly.feature(valve_name, subscribe=True)

class valve:
    def __init__(self):
        client = mqtt.Client()
        print("callback capture set for [%s][%s]" % (state.topic(),problem.topic(),))
        client.message_callback_add(state.topic(), self.on_flow_status)
        client.message_callback_add(problem.topic(), self.on_problem)
        client.on_connect=self.on_connect
        client.loop_start()
        
        try:
            print(valve_name, broker, "mqtt connecting")
            client.connect(broker) 
        except:
            print ("MQTT could not connect",  broker)
            exit
        # this runs forever
        
        topic = open_close.topic()
        open  = open_close.payload_on() 
        close = open_close.payload_off() 
        while True:
            print('enter "o" or "c" to open or close e for stress test ')
            action = input()
            if action == "o":
                print("simulator: publishing topic[%s] payload [%s]" % (topic,open,))
                client.publish(topic, open)
            elif action == "c":
                print("simulator: publishing topic[%s] payload [%s]" % (topic,close,))
                client.publish(topic, close)
            elif action == 'e':
                while True:
                    client.publish(topic, open)
                    time.sleep(10)
                    client.publish(topic, close)
                    time.sleep(10)

    def on_flow_status(self, client, userdata, message):
        print("STATUS [%s]" % (message.payload.decode("utf-8"),))
    
    def on_problem(self, client, userdata, message):
        print("PROBLEM [%s]" % (message.payload.decode("utf-8"),))

    def on_connect(self, client, userdata, flags, rc):
        print("mqtt_manager.on_connect CONNECTED")
        print("subscribing to [%s]" % (state.topic(),))
        client.subscribe(state.topic())
        print("subscribing to [%s]" % (problem.topic(),))
        client.subscribe(problem.topic())

# for testing
print("simulate being a remote valve controler\n")
time.sleep(5)
valve()
    