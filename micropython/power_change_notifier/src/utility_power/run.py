# MIT license copyright 2025 Jim Dodgen
# utility side 
from mqtt_as import MQTTClient, config
import asyncio
import feature_power 
import mqtt_hello
import alert_handler
import cfg
import time
import network

network.hostname(cfg.host_name)
print("I am", network.hostname())

# unusual MQTT code but it works
# this boots up and publishes a" payload_on" in a loop
# There is no payload_off ... this device is plugged in
our_name = "utility_power_status"  # same in generator_power
power_status  = feature_power.feature(our_name,  publish=True)

led = alert_handler.alert_handler(cfg.led_gpio,None)

# Local configuration
def callback(topic_in, msg_in, retained):
    topic = topic_in.decode('utf-8')
    msg = msg_in.decode('utf-8') 
    print("callback: topic [%s] msg [%s]" % (topic, msg,))
        

async def conn_han(client):
    # await client.subscribe(power_status.publish_topic()) 
    # who am I sends a hello 
    hardcoded_generic_description ="utility power monitor, sends status when powered up" 
 # who am I sends a hello 
    print("conn_han: sending hello")
    await mqtt_hello.send_hello(client, our_name, 
                        hardcoded_generic_description, 
                        power_status.get())
    
async def problem_reporter(error_code):
    if error_code >  0:
        led.turn_off()
        await asyncio.sleep(1)
        x = 0
        while x < 1:
            led.flash(count=error_code, duration=0.4, ontime=0.4)
            x += 1
            await asyncio.sleep(1)
        await asyncio.sleep(1)

async def main(client):
    while True:
        print("checking client connection")
        try:
            await client.connect()
        except: 
            print("connect failed")
            error_code = client.status()
            await problem_reporter(error_code)
            pass
        else:
            break
    await asyncio.sleep(2)
    led.flash(1)
    for _ in range(cfg.number_of_cycles_to_run):
        led.turn_on()
        await client.publish(power_status.topic(), power_status.payload_on())
        led.turn_off()
        await asyncio.sleep(4)
    led.turn_off()
    while True:
        await client.publish(power_status.topic(), power_status.payload_on())
        time.sleep(60) # 1 minute
        # subscribers can monitor this to detect a pulse, one per minute
     # when we exit just shutdown and turn off 
     
#config['subs_cb'] = callback
config['subs_cb'] = callback        
config['connect_coro'] = conn_han
config['server'] = cfg.server
config['ssid'] = cfg.ssid
config['wifi_pw'] = cfg.wifi_password
config['problem_reporter'] = problem_reporter

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
