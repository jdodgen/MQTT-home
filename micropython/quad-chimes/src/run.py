# MIT license copyright 2026 Jim Dodgen
# quad chimes
#
VERSION = (1, 2, 1)
import alert_handler
from mqtt_as import MQTTClient, config, MsgQueue
import feature_power
#import mqtt_hello
import alert_handler
import cfg
import time
import asyncio
import time
import os
import switch
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

# ========================
# import asyncio
# from machine import Pin
# from mqtt_as import MQTTClient, config

# async def handle_button(client, btn_flag):
    # while True:
        # await btn_flag.wait()
        # print("Button pressed!")
        # await client.publish('home/button', 'pressed', qos=1)
        # await asyncio.sleep_ms(250)

# async def main(client):
    # await client.connect()
    
    # # 1. Setup button and flag cleanly inside main()
    # button = Pin(14, Pin.IN, Pin.PULL_UP)
    # btn_flag = asyncio.ThreadSafeFlag()
    # button.irq(trigger=Pin.IRQ_FALLING, handler=lambda _: btn_flag.set())
    
    # # 2. Start the task and pass the flag to it
    # asyncio.create_task(handle_button(client, btn_flag))
    
    # while True:
        # await asyncio.sleep(10)

# client = MQTTClient(config)
# try:
    # asyncio.run(main(client))
# finally:
    # client.close()



# ===================
# import asyncio
# from machine import Pin
# from mqtt_as import MQTTClient, config

# # Setup button (assuming active-low with internal pull-up)
# button = Pin(14, Pin.IN, Pin.PULL_UP)
# btn_flag = asyncio.ThreadSafeFlag()

# # Hardware interrupt: runs immediately on press, even if asyncio is busy
# def button_isr(pin):
    # btn_flag.set()

# button.irq(trigger=Pin.IRQ_FALLING, handler=button_isr)

# async def handle_button(client):
    # while True:
        # # Pauses here using 0% CPU until the interrupt fires
        # await btn_flag.wait()
        
        # print("Button pressed! Publishing MQTT message...")
        # await client.publish('home/button', 'pressed', qos=1)
        
        # # Simple debounce delay so one press doesn't trigger multiple times
        # await asyncio.sleep_ms(250)

# async def main(client):
    # await client.connect()
    # # Start your button watcher as a background task
    # asyncio.create_task(handle_button(client))
    
    # # Keep main alive (or run other periodic tasks here)
    # while True:
        # await asyncio.sleep(10)

# # Configure your Wi-Fi and broker settings in config as usual
# client = MQTTClient(config)
# try:
    # asyncio.run(main(client))
# finally:
    # client.close()
# ======================================


SEND_HELLO = home/home_broker/send_hello"
#wildcard_subscribe = feature_power.feature(cfg.cluster_id+"/+", subscribe=True)
#print(wildcard_subscribe.topic())

# conditional formatted print
xprint = print # copy print
def print(*args, **kwargs): # replace print
    #return # comment/uncomment to turn print on off
    xprint("[run]", *args, **kwargs) # the copied real print

# async def send_email(subject, body, cluster_id_only=False):
    # try:
        # smtp = umail.SMTP('smtp.gmail.com', 465, ssl=True)
        # await asyncio.sleep(0)
        # smtp.login(cfg.gmail_user, cfg.gmail_password)
        # await asyncio.sleep(0)
        # smtp.to(cfg.send_messages_to, mail_from=cfg.gmail_user)
        # id = cfg.cluster_id if cluster_id_only else cfg.pretty_name
        # print("our id [%s]" % (id,))
        # smtp.write("CC: %s\nSubject:%s, %s\n\n%s\n" % (cfg.cc_string, subject, id,  body,))
        # await asyncio.sleep(0)
        # smtp.send()
        # await asyncio.sleep(0)
        # smtp.quit()
    # except Exception as e:
            # print("email failed", e)

#
# current_watched_sensors[topic][SUB_TOPICS]
# current_watched_sensors = {}
# SUB_TOPICS
#MESSAGE_THIS_CYCLE = "MTC" # "message_this_cycle"
#HAVE_WE_SENT_POWER_IS_DOWN_EMAIL = "HWSPISE" # "have_we_sent_power_is_down_email"
#PUBLISH_CYCLES_WITHOUT_A_MESSAGE = "PCWAM" # "publish_cycles_without_a_message"
#START_TIME = "ST" # "start_time"
#
# def add_current_watched_sensors(topic):
    # global current_watched_sensors
    # current_watched_sensors[topic] = {
        # MESSAGE_THIS_CYCLE: True,
        # HAVE_WE_SENT_POWER_IS_DOWN_EMAIL: False,
        # PUBLISH_CYCLES_WITHOUT_A_MESSAGE: 0,
        # START_TIME: 0}

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
        elif (topic == SEND_HELLO:
            print("callback hello_request")
            await say_hello(client)
        else:
             print(f"unknown message topic [{topic}] payload [{msg}]")
    print("raw_messages: should never get here, messages exiting?")

# def make_email_body():
    # global current_watched_sensors
    # body = 'Cluster = "%s"\n' %  (cfg.cluster_id,)
    # for topic in current_watched_sensors:
        # name = topic.split("/")[2]
        # try:
            # parts = name.split(" ",1)
            # if len(parts) == 1:
                # parts.append("")
        # except:
            # parts = [name, ""]
        # body += '%s - %s - is %s\n' % (parts[0], parts[1], 
            # "POWERED DOWN" if current_watched_sensors[topic][PUBLISH_CYCLES_WITHOUT_A_MESSAGE] > cfg.other_message_threshold 
            # else "Powered Up")
    # name = cfg.publish.split("/")[2]
    # try:
        # parts = name.split(" ",1)
        # if len(parts) == 1:
            # parts.append("")
    # except:
        # parts = [name, ""]
   # # body += '       # reporting sensor %s - %s]' % (parts[0], parts[1],)
    # print(body)
    # return body

# async def check_for_down_sensors(led_8x8_queue, single_led_queue):
    # global current_watched_sensors
    # should_we_turn_on_led = False
    # need_email = 0
    # sensor_down = []
    # for sensor in  current_watched_sensors:
        # #print("main sensor[%s][%s]" % (sensor, current_watched_sensors[sensor]))
        # if current_watched_sensors[sensor][MESSAGE_THIS_CYCLE] == False:  # no message this cycle
            # if (current_watched_sensors[sensor][PUBLISH_CYCLES_WITHOUT_A_MESSAGE] > cfg.other_message_threshold):
                # if (current_watched_sensors[sensor][PUBLISH_CYCLES_WITHOUT_A_MESSAGE] > 99998):  # this was a dry contact action
                   # sensor_down.append((sensor, True))  
                # else:
                    # sensor_down.append((sensor, False))
                    # if (current_watched_sensors[sensor][START_TIME] == 0):   # did it just start?
                        # if (not current_watched_sensors[sensor][HAVE_WE_SENT_POWER_IS_DOWN_EMAIL]):
                            # need_email += 1
                            # current_watched_sensors[sensor][HAVE_WE_SENT_POWER_IS_DOWN_EMAIL] = True
                            # current_watched_sensors[sensor][START_TIME]= time.time()
            # else:
                # current_watched_sensors[sensor][PUBLISH_CYCLES_WITHOUT_A_MESSAGE] += 1
        # else:  # messages for this topic have arrived
            # current_watched_sensors[sensor][MESSAGE_THIS_CYCLE] = False # set false here, set true in raw_messages
            # current_watched_sensors[sensor][PUBLISH_CYCLES_WITHOUT_A_MESSAGE] = 0
        # #i += 1
        # if current_watched_sensors[sensor][START_TIME] > 0 and sensor in cfg.hard_tracked_topics:
            # should_we_turn_on_led = True
    # if sensor_down:
        # led_8x8_queue.put(sensor_down) # list of problem topics
        # single_led_queue.put("sensor_down")   # LED on solid
    # else:
        # if cfg.led8x8_heartbeat == True:
            # led_8x8_queue.put([("_", False),(".", False)])
            # single_led_queue.put("all_off")
        # else:
            # led_8x8_queue.put([("_", False)])  # this means a blank screen
            # single_led_queue.put("heart_beat")
    # if need_email and cfg.send_email:
        # await send_email("PCN One or more Power Outages or Events", make_email_body(), cluster_id_only=True)

async def handle_button(client, btn_flag):
    while True:
        await btn_flag.wait()
        print("Button pressed!")
        await client.publish('home/button', 'pressed', qos=1)
        await asyncio.sleep_ms(250)
        
async def main():
    global led
   
    
    ## button_press = button.button(cfg.button_pin)
    while True:
        print("checking connection")
        try:
            await client.connect()
        except:
            #pass
            time.sleep(1)
        else:
            break
    led_8x8_queue = None # MsgQueue(20)
    single_led_queue = None # MsgQueue(20)
    # Local configuration, "config" came from mqtt_as
    # wifi set in connect loop
    config['server'] = cfg.broker
    config["user"] = cfg.user
    config["password"] = cfg.password
    config["ssl"] = cfg.ssl
    config["ssl_params"] = {'server_hostname': cfg.broker}
    config["queue_len"] = 10  # Use event interface with default queue size
    # config["response_time"] = 30

    MQTTClient.DEBUG = True  # Optional: print diagnostic messages

    #led_8x8_queue.put([("_",False),(cfg.device_letter,False),("_",False),(cfg.device_letter,False),])
    #single_led_queue.put("boot")
    
    print("creating asyncio tasks")
    #asyncio.create_task(pcn.led_8x8_display(led_8x8_queue))
    #asyncio.create_task(pcn.do_single_led(single_led_queue))
    await asyncio.sleep(2)
    
    #
    # make first connection
    print("make first connection")
    client = await pcn.make_first_connection(config, led_8x8_queue, single_led_queue)
    print("conneted")
    #
    asyncio.create_task(raw_messages(client, led_8x8_queue, single_led_queue))
    asyncio.create_task(pcn.up_so_subscribe(client, led_8x8_queue, single_led_queue, [chime_topic,SEND_HELLO,]))
    asyncio.create_task(pcn.down_report_outage(client, led_8x8_queue, single_led_queue))  
    
     # 1. Setup button and flag cleanly inside main()
    button = machine.Pin(cfg.button_pin, machine.Pin.IN, machine.Pin.PULL_UP)
    btn_flag = asyncio.ThreadSafeFlag()
    button.irq(trigger=Pin.IRQ_FALLING, handler=lambda _: btn_flag.set())
    # 2. Start the task and pass the flag to it
    asyncio.create_task(handle_button(client, btn_flag))      

    # sw = switch.switch(cfg.switch_pin, client)
    # print("switch is",sw.test())
    # if cfg.led8x8_heartbeat == True:
        # led_8x8_queue.put([("_", False),(".", False)])
        # single_led_queue.put("all_off")
    # else:
        # led_8x8_queue.put([("_", False)])
        # single_led_queue.put("heart_beat") # default
    # switch_detected_true_value = True if cfg.switch_type == "NO" else False  # NO Normaly Open
    # switch_on_email_sent = False
    # sw_value = 0; # test fixture
    last_PCN_send = now;
    while True:  # Main loop
        # await asyncio.sleep(0.3)
        # if (button_press.test() == 0):
            # await client.publish(chime_topic, chime_payload)
            # await client.publish(button_topic, "pressed")
            print("button pressed")
        # first publish alive status
        # if cfg.monitor_only == True: # we don't publish or get tracked
            # pass  
        # else:
            # # test fixture
            # # sw_value = not sw_value;
            # sw_value = sw.test()
            # print("switch value", sw_value)
            # print("switch = %s switch_detected_true_value %s" % (sw_value, switch_detected_true_value))
            # if (cfg.switch == True and sw_value != switch_detected_true_value):
                # await client.publish(cfg.publish, "down")
                # if not switch_on_email_sent:  # we have not sent email
                    # switch_on_email_sent = True
                    # # send switch check email
                    # await send_email("(%s) %s %s" % 
                    # (cfg.device_letter, cfg.desc, cfg.switch_subject_event_true), "", cluster_id_only=True)
            # else:
                # print("publishing switch up message")
                # await client.publish(cfg.publish, "up")
                # if switch_on_email_sent:
                    # # email sent so send a now send up email
                    # await send_email("(%s) %s %s" % 
                    # (cfg.device_letter, cfg.desc, cfg.switch_subject_event_false), "", cluster_id_only=True)
                # switch_on_email_sent = False
        # print("\b[publish_check_loop]")
        # await check_for_down_sensors(led_8x8_queue, single_led_queue)
        # if last_PCN_send+number_of_seconds_to_wait < now:
            # last_PCN_send = now;
        await client.publish(PCN_publish_power_topic, "up")
        await asyncio.sleep(number_of_seconds_to_wait)
        

############ startup ###############
time.sleep(cfg.start_delay)
print("starting")
try:
    asyncio.run(main())
finally:
    pass
    #client.close()
print("exiting, should not get here")

