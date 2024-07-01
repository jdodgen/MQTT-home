# MIT Licence copyright Jim Dodgen 2024
# MQTT motorized valve controler.  5 wire version (on, off, sense_open, sense_closed, ground)
#
import os
from universal_mqtt_as import config, MQTTClient, asyncio
import time
import cfg
import water_valve
import feature_toggle
import feature_state
import feature_anomaly
import mqtt_hello
import mqtt_cfg

valve_state = feature_state.feature(  cfg.valve_name, publish=True)
open_close  = feature_toggle.feature( cfg.valve_name, subscribe=True)
problem     = feature_anomaly.feature(cfg.valve_name, publish=True)

# conditional print
xprint = print # copy print
def print(*args, **kwargs): # replace print
    # return
    xprint("[run]", *args, **kwargs) # the copied real print 
      
hardcoded_generic_valve_description ="motor valve controller, with feedback" 
async def say_hello(client):
 # who am I sends a hello 
    print("say_hello: sending hello")
    await mqtt_hello.send_hello(client, cfg.valve_name, 
                        hardcoded_generic_valve_description, 
                        open_close.feature_json(), 
                        valve_state.feature_json(),
                        problem.feature_json())

async def raw_messages(client, water):  # Respond to all incoming messages 
    # loop on message queue
    async for btopic, bmsg, retained in client.queue:
        topic = btopic.decode('utf-8')
        msg = bmsg.decode('utf-8')
        print("callback: topic[%s]" % (topic,))
        if topic == open_close.topic():  # a command to turn valve on or off
            if msg == open_close.payload_on():
                await water.open() 
            else:
                await water.close()
        elif (topic == mqtt_hello.hello_request_topic):
            print("callback hello_request")
            await say_hello(client)

async def check_if_up(client):  # Respond to connectivity being (re)established
    while True:
        await client.up.wait()  # Wait on an Event
        client.up.clear()
        print("check_if_up: up_wait returned")
        await say_hello(client)
        await client.subscribe(open_close.topic())
        await client.subscribe(mqtt_hello.hello_request_topic)   

# async def raw_messages(client, water):  # Respond to all incoming messages 
#     global open_close
#     # loop on message queue
#     async for btopic, bmsg, retained in client.queue:
#         topic = btopic.decode('utf-8')
#         msg = bmsg.decode('utf-8')
#         print("raw_messages topic[%s] payload[%s]" % (topic, msg,))
#         if topic == open_close.topic():  # a command to turn valve on or off
#             if msg == open_close.payload_on():
#                 await water.open() 
#             else:
#                 await water.close()
#     print("should never get here, messages exiting?")

# hardcoded_generic_valve_description ="motor valve controller, with feedback" 
# async def check_if_up(client):  # Respond to connectivity being (re)established
#     while True:
#         await client.up.wait()  # Wait on an Event
#         client.up.clear()
#         print("check_if_up: subscribing  valve")
#         await client.subscribe(open_close.topic())
#         print("check_if_up: publishing hello")
#         await mqtt_hello.send_hello(client, cfg.valve_name, 
#                         hardcoded_generic_valve_description, 
#                         open_close.feature_json(), 
#                         valve_state.feature_json(),
#                         problem.feature_json())
                         
        # h = hello(cfg.valve_name, "motor valve controler, with feedback")
        # h.add_feature(valve.feature_json())
        # h.add_feature(valve_state.feature_json())
        # h.payload()
        # print("hello topic[%s] payload[%s]" % (h.topic(), h.payload()))
        # await client.publish(h.topic(), h.payload()) 

async def main(client):
    water = water_valve.water_valve(client, valve_state, cfg.max_motor_on_time, problem)
    while True:
        print("checking connection")
        try:
            await client.connect()
        except:
            pass
        else:
            break
    # these are loops and run forever
    asyncio.create_task(check_if_up(client))
    asyncio.create_task(raw_messages(client, water))
    while True:
        payload = await water.current_state()
        topic = valve_state.topic()
        print("publish topic [%s] payload [%s]" % (topic, payload,))
        await client.publish(topic, payload) 
        await asyncio.sleep(cfg.time_to_sleep_publish)

time.sleep(5)
print("starting")

# Local mqtt_as configuration
config['ssid']    = mqtt_cfg.ssid  
config['wifi_pw'] = mqtt_cfg.wifi_pw
config['server']  = mqtt_cfg.server 
config["queue_len"] = 1  # Use event interface with default queue size

MQTTClient.DEBUG = True  # Optional: print diagnostic messages
client = MQTTClient(config)
try:
    asyncio.run(main(client))
finally:
    client.close()  # Prevent LmacRxBlk:1 errors
print("example exiting")
