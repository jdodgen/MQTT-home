# MIT license copyright 2025 Jim Dodgen
# Power Change Notifier
# requires only a MQTT Broker. Local or in the Cloud
# All sensor run the identical code, only "cfg.py" is different
# No real limit to the number of sensors. Only  Typical CPU and memory limatations.
# The original application was monitoring utility power and standby (Generator) power
# now monitoring a cluster of things for both power and optionaly the "dry contact" state
# which could be a power state like a solar system or even if a door is open.  
# It monitors and turns on a single or 8x8 LED's and sends emails.
# It publishes status for others to follow, it can be just a listener.
# This is a Simple IoT and a basis for other sensor and action IoT's.
# For any sensor/action this is the most important thing. "am I alive"
# I am using this code as the starting point for other more complex IoT sensors
# example is a "dry_contact" switch option monitoring a gpio line to detect a swich or button:
#
VERSION = (1, 2, 1)
import umail
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

wildcard_subscribe = feature_power.feature(cfg.cluster_id+"/+", subscribe=True)
print(wildcard_subscribe.topic())

# conditional formatted print
xprint = print # copy print
def print(*args, **kwargs): # replace print
    #return # comment/uncomment to turn print on off
    xprint("[run]", *args, **kwargs) # the copied real print

async def send_email(subject, body, cluster_id_only=False):
    try:
        smtp = umail.SMTP('smtp.gmail.com', 465, ssl=True)
        await asyncio.sleep(0)
        smtp.login(cfg.gmail_user, cfg.gmail_password)
        await asyncio.sleep(0)
        smtp.to(cfg.send_messages_to, mail_from=cfg.gmail_user)
        id = cfg.cluster_id if cluster_id_only else cfg.pretty_name
        print("our id [%s]" % (id,))
        smtp.write("CC: %s\nSubject:%s, %s\n\n%s\n" % (cfg.cc_string, subject, id,  body,))
        await asyncio.sleep(0)
        smtp.send()
        await asyncio.sleep(0)
        smtp.quit()
    except Exception as e:
            print("email failed", e)

#
# current_watched_sensors[topic][SUB_TOPICS]
current_watched_sensors = {}
# SUB_TOPICS
MESSAGE_THIS_CYCLE = "MTC" # "message_this_cycle"
HAVE_WE_SENT_POWER_IS_DOWN_EMAIL = "HWSPISE" # "have_we_sent_power_is_down_email"
PUBLISH_CYCLES_WITHOUT_A_MESSAGE = "PCWAM" # "publish_cycles_without_a_message"
START_TIME = "ST" # "start_time"
#
def add_current_watched_sensors(topic):
    global current_watched_sensors
    current_watched_sensors[topic] = {
        MESSAGE_THIS_CYCLE: True,
        HAVE_WE_SENT_POWER_IS_DOWN_EMAIL: False,
        PUBLISH_CYCLES_WITHOUT_A_MESSAGE: 0,
        START_TIME: 0}

async def raw_messages(client,led_8x8_queue, single_led_queue):  # Process all incoming messages
    # global led
    global current_watched_sensors
    # global other_status
    # loop on message queue
    print("raw_messages starting")
    async for btopic, bmsg, retained in client.queue:
        topic = btopic.decode('utf-8')
        msg = bmsg.decode('utf-8')
        print("callback [%s][%s] retained[%s]" % (topic, msg, retained,))
        #if topic == our_status.topic():  # It is me!
            # print("raw_messages bypassing", topic)
            #continue
        # i=0
        restored_sensors = ""
        if topic not in current_watched_sensors:
            add_current_watched_sensors(topic)
        else:
            if msg == "down":  # this is from a switch/button/dry contacts
                current_watched_sensors[topic][MESSAGE_THIS_CYCLE] = False  # act like this sensor is down
                check_sensors = True if current_watched_sensors[topic][PUBLISH_CYCLES_WITHOUT_A_MESSAGE] < 99998 else False                    
                current_watched_sensors[topic][PUBLISH_CYCLES_WITHOUT_A_MESSAGE] = 99999  # force a down condition in check_sensors
                if check_sensors:
                    await check_for_down_sensors(led_8x8_queue, single_led_queue)
            else:    
                current_watched_sensors[topic][MESSAGE_THIS_CYCLE] = True
                if current_watched_sensors[topic][HAVE_WE_SENT_POWER_IS_DOWN_EMAIL]:
                    current_watched_sensors[topic][HAVE_WE_SENT_POWER_IS_DOWN_EMAIL] = False
                    current_watched_sensors[topic][PUBLISH_CYCLES_WITHOUT_A_MESSAGE] = 0
                    seconds = time.time() - current_watched_sensors[topic][START_TIME]
                    hours = seconds/3600
                    minutes = seconds/60
                    restored_sensors +=  ("# Power restored to [%s]\n# Down, Minutes: %.f (Hours: %.1f)\n" %
                        (topic.split("/")[2], minutes, hours))
                current_watched_sensors[topic][START_TIME]=0
        if restored_sensors: 
            await check_for_down_sensors(led_8x8_queue, single_led_queue)
            if cfg.send_email:
                await send_email("PCN Power restored or Event cleared: %s" % (topic.split("/")[2],),  restored_sensors+make_email_body())
            
    print("raw_messages exiting?")

def make_email_body():
    global current_watched_sensors
    body = 'Cluster = "%s"\n' %  (cfg.cluster_id,)
    for topic in current_watched_sensors:
        name = topic.split("/")[2]
        try:
            parts = name.split(" ",1)
            if len(parts) == 1:
                parts.append("")
        except:
            parts = [name, ""]
        body += '%s - %s - is %s\n' % (parts[0], parts[1], 
            "POWERED DOWN" if current_watched_sensors[topic][PUBLISH_CYCLES_WITHOUT_A_MESSAGE] > cfg.other_message_threshold 
            else "Powered Up")
    name = cfg.publish.split("/")[2]
    try:
        parts = name.split(" ",1)
        if len(parts) == 1:
            parts.append("")
    except:
        parts = [name, ""]
   # body += '       # reporting sensor %s - %s]' % (parts[0], parts[1],)
    print(body)
    return body

# async def up_so_subscribe(client, led_8x8_queue, single_led_queue):
    # wild_topic = wildcard_subscribe.topic()
    # while True:
        # await client.up.wait()
        # client.up.clear()
        # print('doing subscribes', wild_topic)
        # led_8x8_queue.put((("all_off",False), ))
        # single_led_queue.put("all_off")
        # await client.subscribe(wildcard_subscribe.topic())
        # print("emailing startup")
        # await send_email("PCN Starting", boilerplate)

# async def down_report_outage(client, led_8x8_queue, single_led_queue):
    # while True:
        # await client.down.wait()
        # client.down.clear()
        # print('got outage')
        # machine.soft_reset()   # 
        # #led_8x8_queue.put((("wifi",False),))
        # #single_led_queue.put("5")

async def check_for_down_sensors(led_8x8_queue, single_led_queue):
    global current_watched_sensors
    should_we_turn_on_led = False
    need_email = 0
    sensor_down = []
    for sensor in  current_watched_sensors:
        #print("main sensor[%s][%s]" % (sensor, current_watched_sensors[sensor]))
        if current_watched_sensors[sensor][MESSAGE_THIS_CYCLE] == False:  # no message this cycle
            if (current_watched_sensors[sensor][PUBLISH_CYCLES_WITHOUT_A_MESSAGE] > cfg.other_message_threshold):
                if (current_watched_sensors[sensor][PUBLISH_CYCLES_WITHOUT_A_MESSAGE] > 99998):  # this was a dry contact action
                   sensor_down.append((sensor, True))  
                else:
                    sensor_down.append((sensor, False))
                    if (current_watched_sensors[sensor][START_TIME] == 0):   # did it just start?
                        if (not current_watched_sensors[sensor][HAVE_WE_SENT_POWER_IS_DOWN_EMAIL]):
                            need_email += 1
                            current_watched_sensors[sensor][HAVE_WE_SENT_POWER_IS_DOWN_EMAIL] = True
                            current_watched_sensors[sensor][START_TIME]= time.time()
            else:
                current_watched_sensors[sensor][PUBLISH_CYCLES_WITHOUT_A_MESSAGE] += 1
        else:  # messages for this topic have arrived
            current_watched_sensors[sensor][MESSAGE_THIS_CYCLE] = False # set false here, set true in raw_messages
            current_watched_sensors[sensor][PUBLISH_CYCLES_WITHOUT_A_MESSAGE] = 0
        #i += 1
        if current_watched_sensors[sensor][START_TIME] > 0 and sensor in cfg.hard_tracked_topics:
            should_we_turn_on_led = True
    if sensor_down:
        led_8x8_queue.put(sensor_down) # list of problem topics
        single_led_queue.put("sensor_down")   # LED on solid
    else:
        led_8x8_queue.put([("_", False),(".", False)])
        single_led_queue.put("heart_beat")
    if need_email and cfg.send_email:
        await send_email("PCN One or more Power Outages or Events", make_email_body(), cluster_id_only=True)

async def main():
    global led
    pcn.print_flash_usage()
    for topic in cfg.hard_tracked_topics: # "hard" tracked topics are monitored from boot,  "soft" only after a publish
        add_current_watched_sensors(topic)
    led_8x8_queue = MsgQueue(20)
    single_led_queue = MsgQueue(20)
    # Local configuration, "config" came from mqtt_as
    # wifi set in connect loop
    config['server'] = cfg.broker
    config["user"] = cfg.user
    config["password"] = cfg.password
    config["ssl"] = True
    config["ssl_params"] = {'server_hostname': cfg.broker}
    config["queue_len"] = 10  # Use event interface with default queue size
    # config["response_time"] = 30

    MQTTClient.DEBUG = True  # Optional: print diagnostic messages

    led_8x8_queue.put([("_",False),(cfg.device_letter,False),("_",False),(cfg.device_letter,False),])
    single_led_queue.put("boot")
    
    print("creating asyncio tasks")
    asyncio.create_task(pcn.led_8x8_display(led_8x8_queue))
    asyncio.create_task(pcn.do_single_led(single_led_queue))
    await asyncio.sleep(2)
    
    #
    # make first connection
    print("make first connection")
    client = await pcn.make_first_connection(config, led_8x8_queue, single_led_queue)
    print("conneted")
    #
    asyncio.create_task(raw_messages(client, led_8x8_queue, single_led_queue))
    asyncio.create_task(pcn.up_so_subscribe(client, led_8x8_queue, single_led_queue, [wildcard_subscribe.topic(),]))
    asyncio.create_task(pcn.down_report_outage(client, led_8x8_queue, single_led_queue))        

    sw = switch.switch(cfg.switch_pin, client)
    print("switch is",sw.test())
    if cfg.no_heartbeat == True:
        led_8x8_queue.put([("_", False)])
    else:
        led_8x8_queue.put([("_", False),(".", False)])
    single_led_queue.put("heart_beat")
    switch_detected_true_value = True if cfg.switch_type == "NO" else False  # NO Normaly Open
    switch_on_email_sent = False
    sw_value = 0; # test fixture
    while True:  # Main loop checking to see of other has published
        # first publish alive status
        if cfg.monitor_only == True: # we don't publish or get tracked
            pass  
        else:
            # test fixture
            # sw_value = not sw_value;
            sw_value = sw.test()
            print("switch value", sw_value)
            print("switch = %s switch_detected_true_value %s" % (sw_value, switch_detected_true_value))
            if (cfg.switch == True and sw_value != switch_detected_true_value):
                await client.publish(cfg.publish, "down")
                if not switch_on_email_sent and cfg.send_start_email:  # we have not sent email
                    switch_on_email_sent = True
                    # send switch check email
                    await send_email("(%s) %s %s" % 
                    (cfg.device_letter, cfg.desc, cfg.switch_subject_event_true), "", cluster_id_only=True)
            else:
                print("publishing switch up message")
                await client.publish(cfg.publish, "up")
                if switch_on_email_sent:
                    # email sent so send a now send up email
                    await send_email("(%s) %s %s" % 
                    (cfg.device_letter, cfg.desc, cfg.switch_subject_event_false), "", cluster_id_only=True)
                switch_on_email_sent = False
        print("\b[publish_check_loop]")
        await check_for_down_sensors(led_8x8_queue, single_led_queue)
        await asyncio.sleep(cfg.number_of_seconds_to_wait)

############ startup ###############
time.sleep(cfg.start_delay)
print("starting")
try:
    asyncio.run(main())
finally:
    pass
    #client.close()
print("exiting, should not get here")

