# MIT License copyright Jim Dodgen 2024
# MQTT motorized valve controller.  5 wire version (on, off, sense_open, sense_closed, ground)
#
#from  universal_mqtt_as import MQTTClient, config,  asyncio 
import uasyncio as asyncio  # micropython version 
import mqtt_as
import time
import cfg
# library stuff
import feature_ding_ding
import feature_ding_dong
import feature_westminster
import feature_button
import feature_three_chimes
import mqtt_hello
# our code
import chime
import button

ding_ding =    feature_ding_ding.feature(cfg.name,         subscribe=True)
ding_dong =    feature_ding_dong.feature(cfg.name,         subscribe=True)
westminster =  feature_westminster.feature(cfg.name,       subscribe=True)
three_chimes = feature_three_chimes.feature(cfg.name,      subscribe=True)
btn =          feature_button.feature(cfg.name,            publish=True)


c = chime.chime()

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

async def raw_messages(client):  # Respond to all incoming messages 
    global open_close
    # loop on message queue
    async for btopic, bmsg, retained in client.queue:
        topic = btopic.decode('utf-8')
        msg = bmsg.decode('utf-8')
        print("raw_messages topic[%s] payload[%s]" % (topic, msg,))
        if topic == ding_ding.topic():    
               c.ding_ding()
        elif topic == ding_dong.topic():    
               c.ding_dong()
        elif topic == westminster.topic():    
               c.westminster()
        elif topic == three_chimes.topic():    
               c.play_all()
        elif (topic == mqtt_hello.hello_request_topic):
            print("callback hello_request")
            await say_hello(client)
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

async def main(client):
    button_press = button.button(cfg.button_pin)
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
    asyncio.create_task(raw_messages(client))
    #
    # was a IRQ handler to report button.
    # 
    # Loop
    while True:
        await asyncio.sleep(0.3)
        if (button_press.test() == 0):
            await client.publish(button.topic(), button.payload_on())
#
# start up
#
time.sleep(5)
print("starting: ssid[%s] pw[%s] broker[%s]" % (cfg.ssid, cfg.wifi_password, cfg.server,))

# Local mqtt_as configuration
mqtt_as.config['ssid']    = cfg.ssid  
mqtt_as.config['wifi_pw'] = cfg.wifi_password
mqtt_as.config['server']  = cfg.server 
mqtt_as.config["queue_len"] = 1  # Use event interface with default queue size

mqtt_as.DEBUG = True  # Optional: print diagnostic messages
client = mqtt_as.MQTTClient(mqtt_as.config)
try:
    asyncio.run(main(client))
finally:
    client.close()
print("should not get here?")
