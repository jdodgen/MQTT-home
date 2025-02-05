# MIT license copyright 2024 Jim Dodgen

from mqtt_as import MQTTClient, config
import asyncio
from  feature_power import feature_power
from mqtt_hello import hello
import alert_handler
import cfg
import time

# unusual MQTT code but it works
# this boots up and publishes a" payload_on" in a loop
# There is no payload_off ... this device is plugged in

power_status  = feature_power("utility_power_status")
led = alert_handler.alert_handler(cfg.led_gpio, None)

# Local configuration
def callback(topic_in, msg_in, retained):
    topic = topic_in.decode('utf-8')
    msg = msg_in.decode('utf-8') 
    print("callback: topic [%s] msg [%s]" % (topic, msg,))
        

async def conn_han(client):
    # await client.subscribe(power_status.publish_topic()) 
    # who am I sends a hello 
    h = hello("utility_power_status", "When running publishes \"power on\" in a loop, quits in an hour after boot")
    h.add_feature(power_status.feature_json())
    h.payload()
    print("hello topic[%s] payload[%s]" % (h.topic(), h.payload()))
    await client.publish(h.topic(), h.payload()) 
  
async def main(client):
    while True:
        print("checking client connection")
        try:
            await client.connect()
        except Exception as e: 
            print(e)
            await asyncio.sleep(1)
        else:
            break
    led.flash(3)
    for _ in range(cfg.number_of_cycles_to_run):
        led.turn_on()
        await client.publish(power_status.publish_topic(), power_status.payload_on())
        led.turn_off()
        time.sleep(1) 
    led.turn_off()
    while True:
        await client.publish(power_status.publish_topic(), power_status.payload_on())
        time.sleep(10*60) # ten minutes ... just for status
        # also incase gen wall wart is power cycled
     # when we exit just shutdown and turn off 
     
#config['subs_cb'] = callback
config['subs_cb'] = callback        
config['connect_coro'] = conn_han
config['server'] = cfg.server
config['ssid'] = cfg.ssid
config['wifi_pw'] = cfg.wifi_password

led.flash(2)  # I'm alive
time.sleep(2)
led.turn_on() #  MQTT stuff
MQTTClient.DEBUG = True  # Optional: print diagnostic messages
client = MQTTClient(config)
led.turn_off()
try:
    asyncio.run(main(client))
finally:
    client.close()  # Prevent LmacRxBlk:1 errors
