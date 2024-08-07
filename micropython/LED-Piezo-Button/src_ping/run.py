# MIT license copyright 2024 Jim Dodgen
#
# version 3 3/16/2024
#
import alert_handler
from mqtt_as import MQTTClient, config
import uasyncio as asyncio   # version for micropython
import feature_alert
import mqtt_cfg
import time
import mqtt_hello

our_name = "ping_tool"

# esp32-s2 mini pins
led_pin = 3
piezo_pin = 11
button_pin = 7

alert  = feature_alert.feature("hot_water_controller",publish = True)
ah     = alert_handler.alert_handler(led_pin=led_pin, piezo_pin=piezo_pin)
 
# conditional print
xprint = print # copy print
def print(*args, **kwargs): # replace print
    #return # comment/uncomment to turn print on off
    # do whatever you want to do
    #xprint('statement before print')
    xprint("[run]", *args, **kwargs) # the copied real print

async def say_hello(client):
 # who am I sends a hello 
    print("say_hello: sending hello")
    await mqtt_hello.send_hello(client, our_name, 
            "flash and beep when pinging", 
            alert.get(),
            )

async def raw_messages(client):  # Respond to all incoming messages 
    # loop on message queue
    async for btopic, bmsg, retained in client.queue:
        topic = btopic.decode('utf-8')
        msg = bmsg.decode('utf-8')
        print("callback: topic[%s]" % (topic,))
     
        if (topic == mqtt_hello.hello_request_topic):
            print("callback hello_request")
            await say_hello(client)

async def check_if_up(client):  # Respond to connectivity being (re)established
    while True:
        await client.up.wait()  # Wait on an Event
        client.up.clear()
        print("check_if_up: up_wait returned")
        await say_hello(client)
        await client.subscribe(alert.topic())
        await client.subscribe(mqtt_hello.hello_request_topic)                  

async def main(client):
    
        
    ah.flash(count=4) # lets you know it has booted

    while True:
        print("checking connection")
        try:
            await client.connect()
        except:
            time.sleep(1)
            pass
        else:
            break
    # these are loops and run forever
    asyncio.create_task(check_if_up(client))
    asyncio.create_task(raw_messages(client))

    await client.subscribe(alert.topic())
    await client.subscribe(mqtt_hello.hello_request_topic)                  
    while True:
        await asyncio.sleep(1)
        await client.publish(alert.topic(), alert.topic().payload_on())
        ah.flash(count=1)
        a.beep()

time.sleep(5)
print("starting")
# Local configuration, "config" came from mqtt_as
config['server'] = mqtt_cfg.server
# Required on Pyboard D and ESP32. On ESP8266 these may be omitted (see above).
config['ssid'] = mqtt_cfg.ssid
config['wifi_pw'] = mqtt_cfg.wifi_pw
config["queue_len"] = 1  # Use event interface with default queue size

MQTTClient.DEBUG = True  # Optional: print diagnostic messages
client = MQTTClient(config)
try:
    asyncio.run(main(client))
finally:
    client.close()
print("example exiting")
