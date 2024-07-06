# MIT License copyright Jim Dodgen 2024
# MQTT motorized valve controller.  5 wire version (on, off, sense_open, sense_closed, ground)
#
#from  universal_mqtt_as import MQTTClient, config,  asyncio 
import uasyncio as asyncio  # micropython version 
import mqtt_as
import time
import machine
import cfg
import mqtt_cfg
# library stuff
import feature_ding_ding
import feature_ding_dong
import feature_westminster
import feature_button
import feature_three_chimes
import mqtt_hello
# our code
#import chime
import button

ding_ding =    feature_ding_ding.feature(cfg.name,         subscribe=True)
ding_dong =    feature_ding_dong.feature(cfg.name,         subscribe=True)
westminster =  feature_westminster.feature(cfg.name,       subscribe=True)
three_chimes = feature_three_chimes.feature(cfg.name,      subscribe=True)
btn =          feature_button.feature(cfg.name,            publish=True)
pin_play_all      = machine.Pin(cfg.play_all_pin,     machine.Pin.OUT)
pin_ding_dong     = machine.Pin(cfg.ding_dong_pin,    machine.Pin.OUT)
pin_ding_ding     = machine.Pin(cfg.ding_ding_pin,    machine.Pin.OUT)
pin_west          = machine.Pin(cfg.westminster_pin,  machine.Pin.OUT)  
pin_play_all.value(1)
pin_ding_dong.value(1)
pin_ding_ding.value(1)
pin_west.value(1)
# set this to None if you do not want a default sound for the button press
# default_chime = None
default_chime = pin_west
# conditional print
xprint = print # copy print
def print(*args, **kwargs): # replace print
    # return
    xprint("[run]", *args, **kwargs) # the copied real print    

hardcoded_generic_description ="Four different chimes and a button" 
async def say_hello(client):
 # who am I sends a hello 
    print("say_hello: sending hello")
    await mqtt_hello.send_hello(client, cfg.name, 
                        hardcoded_generic_description, 
                        ding_ding.get(),
                        ding_dong.get(),
                        westminster.get(),
                        three_chimes.get(),
                        btn.get(), 
                        )
#quad_chime = chime.chime()

async def raw_messages(client):  # Respond to all incoming messages 
    
    # loop on message queue
    async for btopic, bmsg, retained in client.queue:
        topic = btopic.decode('utf-8')
        msg = bmsg.decode('utf-8')
        print("raw_messages topic[%s] payload[%s]" % (topic, msg,))
        if topic == ding_ding.topic(): 
            print("chiming ...ding_ding")    
            pin_ding_ding.value(0)
            await asyncio.sleep(1)
            pin_ding_ding.value(1)
            print("... chimed")
        elif topic == ding_dong.topic():    
            print("chiming ...ding_dong")    
            pin_ding_dong.value(0)
            await asyncio.sleep(1)
            pin_ding_dong.value(1)
            print("... chimed")
        elif (topic == westminster.topic()): 
            print("chiming ...westminster")    
            pin_west.value(0)
            await asyncio.sleep(1)
            pin_west.value(1)
            print("... chimed")
        elif (topic == three_chimes.topic()):    
            print("chiming ...play_all")     
            pin_play_all.value(0)
            await asyncio.sleep(1)
            pin_play_all.value(1)
            print("... chimed")
        elif (topic == btn.topic() and default_chime):
            print("chiming ...default_chime")     
            default_chime.value(0)
            await asyncio.sleep(1)
            default_chime.value(1)
            print("... chimed")  
        elif (topic == mqtt_hello.hello_request_topic):
            print("callback hello_request")
            await say_hello(client)
        else:
             print("unknown message")
    print("should never get here, messages exiting?")

hardcoded_generic_description ="Four different chimes and a button" 
async def check_if_up(client):  # Respond to connectivity being (re)established
    while True:
        await client.up.wait()  # Wait on an Event
        client.up.clear()
        print("check_if_up: up_wait returned, doing pub/sub ")
        await say_hello(client)
        await client.subscribe(ding_ding.topic())
        await client.subscribe(ding_dong.topic())
        await client.subscribe(westminster.topic())
        await client.subscribe(three_chimes.topic()) 
        if default_chime:
            await client.subscribe(btn.topic())   
        await client.subscribe(mqtt_hello.hello_request_topic)  

async def main(client):
    button_press = button.button(cfg.button_pin)
    while True:
        print("checking connection")
        try:
            await client.connect()
        except:
            #pass
            time.sleep(1)
        else:
            break
    # these are loops and run forever
    asyncio.create_task(check_if_up(client))
    asyncio.create_task(raw_messages(client))
    #
    # was a IRQ handler to report button.
    # 
    # Loop
    while True:
        await asyncio.sleep(0.3)
        if (button_press.test() == 0):
            await client.publish(btn.topic(), btn.payload_on())
            print("button pressed")
#
# start up
#
time.sleep(5)
print("starting: ssid[%s] pw[%s] broker[%s]" % (mqtt_cfg.ssid, mqtt_cfg.wifi_pw, mqtt_cfg.server,))

# Local mqtt_as configuration
mqtt_as.config['ssid']    = mqtt_cfg.ssid  
mqtt_as.config['wifi_pw'] = mqtt_cfg.wifi_pw
mqtt_as.config['server']  = mqtt_cfg.server 
mqtt_as.config["queue_len"] = 1  # Use event interface with default queue size

mqtt_as.DEBUG = True  # Optional: print diagnostic messages
client = mqtt_as.MQTTClient(mqtt_as.config)
try:
    asyncio.run(main(client))
finally:
    client.close()
print("should not get here?")
