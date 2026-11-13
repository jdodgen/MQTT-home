# MIT license copyright 2026 Jim Dodgen
# quad chimes
#
VERSION = (1, 3, 1)
from mqtt_as import MQTTClient, config, MsgQueue
import cfg
import time
import asyncio
import os
import machine
import pcn

pin_play_all      = machine.Pin(cfg.play_all_pin,     machine.Pin.OUT)
pin_ding_dong     = machine.Pin(cfg.ding_dong_pin,    machine.Pin.OUT)
pin_ding_ding     = machine.Pin(cfg.ding_ding_pin,    machine.Pin.OUT)
pin_west          = machine.Pin(cfg.westminster_pin,  machine.Pin.OUT)  
pin_play_all.value(1)
pin_ding_dong.value(1)
pin_ding_ding.value(1)
pin_west.value(1)

SEND_HELLO = "home/home_broker/send_hello"

# conditional formatted print
xprint = print # copy print
def print(*args, **kwargs): # replace print
    #return # comment/uncomment to turn print on off
    xprint("[run]", *args, **kwargs) # the copied real print

async def raw_messages(client):  # Respond to all incoming messages 
    # loop on message queue
    async for btopic, bmsg, retained in client.queue:
        topic = btopic.decode('utf-8')
        msg = bmsg.decode('utf-8')
        print("raw_messages topic[%s] payload[%s]" % (topic, msg,))
        if topic == cfg.chime_topic: 
            if msg == "ding_ding":
                print("chiming ...ding_ding")    
                pin_ding_ding.value(0)
                await asyncio.sleep(1)
                pin_ding_ding.value(1)
            elif msg == "ding_dong":  
                print("chiming ...ding_dong")    
                pin_ding_dong.value(0)
                await asyncio.sleep(1)
                pin_ding_dong.value(1)
            elif msg == "westminster": 
                print("chiming ...westminster")    
                pin_west.value(0)
                await asyncio.sleep(1)
                pin_west.value(1)
            elif msg == "three_chimes":     
                print("chiming ...play_all")     
                pin_play_all.value(0)
                await asyncio.sleep(1)
                pin_play_all.value(1)
            else:
                print(f"unknown payload: topic [{topic}] payload [{msg}]")
        elif (topic == SEND_HELLO):
            print("callback hello_request")
            await say_hello(client)
        else:
             print(f"unknown message topic [{topic}] payload [{msg}]")
    print("raw_messages: should never get here, messages exiting?")

async def handle_button(client, btn_flag):
    while True:
        await btn_flag.wait()
        btn_flag.clear()
        print("Button pressed!")
        await client.publish(cfg.chime_topic, cfg.chime_payload)
        await client.publish(cfg.button_topic, "pressed")
        await asyncio.sleep(1)
        btn_flag.clear()
        
async def main():
    # global led
    led_8x8_queue = None # MsgQueue(20)
    single_led_queue = None # MsgQueue(20)
    config['server'] = cfg.broker
    config["user"] = cfg.user
    config["password"] = cfg.password
    config["ssl"] = cfg.ssl
    config["ssl_params"] = {'server_hostname': cfg.broker}
    config["queue_len"] = 10  # Use event interface with default queue size
    print("make first connection")
    client = await pcn.make_first_connection(config, led_8x8_queue, single_led_queue)
    print("conneted")
    
    MQTTClient.DEBUG = True  # Optional: print diagnostic messages
    
    print("creating asyncio tasks")
    
    await asyncio.sleep(2)
 
    asyncio.create_task(raw_messages(client))
    asyncio.create_task(pcn.up_so_subscribe(client, led_8x8_queue, single_led_queue, [cfg.chime_topic, SEND_HELLO,]))
    asyncio.create_task(pcn.down_report_outage(client, led_8x8_queue, single_led_queue))  
    
     # 1. Setup button and flag cleanly inside main()
    button = machine.Pin(cfg.button_pin, machine.Pin.IN, machine.Pin.PULL_UP)
    btn_flag = asyncio.ThreadSafeFlag()
    button.irq(trigger=machine.Pin.IRQ_FALLING, handler=lambda _: btn_flag.set())
    # 2. Start the task and pass the flag to it
    asyncio.create_task(handle_button(client, btn_flag))      

    while True:  # Main loop
        await client.publish(cfg.PCN_publish_power_topic, "up")
        await asyncio.sleep(cfg.number_of_seconds_to_wait)

############ startup ###############
print("starting")
try:
    asyncio.run(main())
finally:
    pass
    #client.close()
print("exiting, should not get here")

