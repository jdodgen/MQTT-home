# this execsizes the door_bell IoT
# Copyright Jim Dodgen 2023 MIT License
import path_fix

import feature_ding_ding
import feature_ding_dong
import feature_westminster
import feature_three_chimes
import feature_button
import paho.mqtt.client as mqtt
import time
import cfg

broker     = "192.168.0.193"

# features 
ding_ding = feature_ding_ding.feature(cfg.name, publish=True)
ding_dong = feature_ding_dong.feature(cfg.name, publish=True)
westminster = feature_westminster.feature(cfg.name, publish=True)
three_chimes = feature_three_chimes.feature(cfg.name, publish=True)
button = feature_button.feature(cfg.name, subscribe=True)

class door_bell:
    def __init__(self):
        client = mqtt.Client()
        print("callback capture set for [%s]" % (button.topic(),))
        client.message_callback_add(button.topic(), self.on_button_press)
        client.on_connect=self.on_connect
        client.loop_start()
        
        try:
            print(cfg.name, broker, "mqtt connecting")
            client.connect(broker) 
        except:
            print ("MQTT could not connect",  broker)
            exit
        # this runs forever
        
        while True:
            print('enter "i", "w", "a" or "o"')
            action = input()
            if action == "o":
                print("simulator: publishing topic[%s] payload [%s]" % (ding_dong.topic(),ding_dong.payload_on(),))
                client.publish(ding_dong.topic(), ding_dong.payload_on())
            elif action == "i":
                print("simulator: publishing topic[%s] payload [%s]" % (ding_ding.topic(),ding_ding.payload_on(),))
                client.publish(ding_ding.topic(), ding_ding.payload_on())
            elif action == 'w':
                print("simulator: publishing topic[%s] payload [%s]" % (westminster.topic(),westminster.payload_on(),))
                client.publish(westminster.topic(), westminster.payload_on())
            elif action == 'a':
                print("simulator: publishing topic[%s] payload [%s]" % (westminster.topic(),westminster.payload_on(),))
                client.publish(three_chimes.topic(), three_chimes.payload_on())

    def on_button_press(self, client, userdata, message):
        print("button press [%s]" % (message.payload.decode("utf-8"),))

    def on_connect(self, client, userdata, flags, rc):
        print("mqtt_manager.on_connect CONNECTED")
        print("subscribing to [%s]" % (button.topic(),))
        client.subscribe(button.topic())

# for testing
print("exercise [%s] Iot\n" % (cfg.name,))
time.sleep(5)
door_bell()
    