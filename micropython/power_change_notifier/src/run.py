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
VERSION = (1, 0, 1)
import umail
import alert_handler
from mqtt_as import MQTTClient, config
import feature_power
#import mqtt_hello
import alert_handler
import cfg
import tm1640
import time
import asyncio
import time
import os
import switch
from msgqueue import  MsgQueue

wildcard_subscribe = feature_power.feature(cfg.cluster_id+"/+", subscribe=True)
print(wildcard_subscribe.topic())

#our_status = feature_power.feature(cfg.cluster_id+"/"+cfg.publish, publish=True)   # publisher
# print("Our topic = [%s]" % (our_status.topic(),))

# ERRORS
boilerplate = '''Starting up ...\nFor reference:
Flashing LED error codes
1 Hello, starting up
2 ERROR_AP_NOT_FOUND or
  ERROR_BAD_PASSWORD
3 ERROR_BROKER_LOOKUP_FAILED or
  ERROR_BROKER_CONNECT_FAILED
5 Runtime failure, re-connecting
LED solid on or letter on 8x8, indicates an outage.
LED out, normal no outage
'''

# conditional formatted print
xprint = print # copy print
def print(*args, **kwargs): # replace print
    #return # comment/uncomment to turn print on off
    xprint("[run]", *args, **kwargs) # the copied real print

async def send_email(subject, body, cluster_id_only=False):
    if cfg.send_email:
        try:
            smtp = umail.SMTP('smtp.gmail.com', 465, ssl=True)
            await asyncio.sleep(0)
            smtp.login(cfg.gmail_user, cfg.gmail_password)
            await asyncio.sleep(0)
            smtp.to(cfg.send_messages_to, mail_from=cfg.gmail_user)
            id = cfg.cluster_id if cluster_id_only else cfg.publish
            print("our id [%s]" % (id,))
            smtp.write("CC: %s\nSubject:PCN %s, %s\n\n%s\n" % (cfg.cc_string, subject, id,  body,))
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
            await send_email("Power restored", restored_sensors+make_email_body())
            
    print("raw_messages exiting?")

def print_flash_usage():
    import esp
    stat = os.statvfs('/')
    total_size = stat[1] * stat[2]
    free_space = stat[0] * stat[3]
    used_space = total_size - free_space
    print("Flash: total %d used %s free %d" % (total_size,used_space,free_space,))
    flash_size = esp.flash_size()
    flash_user_start = esp.flash_user_start()
    print("ESP flash: total %d used  %d free %d" % (flash_size, flash_user_start, flash_size-flash_user_start))

# show PSRAM messages.
async def _memory(self):
    import gc
    import os
    while True:
        await asyncio.sleep(20)
        gc.collect()
        print("RAM free %d alloc %d" % (gc.mem_free(), gc.mem_alloc(),))
        
def get_8x8_matrix(string):
    try:
        item = cfg.tm1640_chars[string] # might be a full word match like boot1
    except:
        try:
            item = cfg.tm1640_chars[string[0]] # Just lookup the first char
        except:
            print("get_8x8_matrix not found in cfg.tm1640_chars", string)
            item = cfg.tm1640_chars["?"]
    print("get_8x8_matrix [%s] returning [%s]" % (string,item))
    return item

class display8x8:
    def __init__(self, clk=14, dio=13, bright=7):
        if clk is None:
            self.ignore = True
            return
        else:
            self.ignore = False
        import tm1640
        from machine import Pin
        self.tm = tm1640.TM1640(clk=Pin(clk), dio=Pin(dio))
        # all LEDs bright
        self.tm.brightness(bright)

    def write(self, bit_map):
        if self.ignore is False:
            self.tm.write(bit_map)

async def do_single_led(single_led_queue):
    led = alert_handler.alert_handler(cfg.led_gpio, None, onboard_led_pin=cfg.onboard_led_gpio)
    async for cmd,  in single_led_queue:
        while not single_led_queue.empty(): # flush the queue, use last item
            async for cmd, in single_led_queue:
                break
        print("do_single_led [%s]" % (cmd,))
        if cmd == "all_off":
            led.turn_off()
        elif cmd == "boot":
            led.turn_on()
            await asyncio.sleep(1)
            led.turn_off()
        elif cmd == "sensor_down":
            led.turn_on()
        else:
            flash_count = 4
            if cmd == "wifi":
                flash_count = 2
            elif cmd == "broker":
                flash_count = 3
            elif cmd == "outage":
                flash_count = 6
            while single_led_queue.empty():
                await led.async_flash(count=flash_count, duration=0.5, ontime=0.5)
                await asyncio.sleep(1)

class do_8x8_list:
    def __init__(self, led_8x8_queue):
        self.led_8x8_queue = led_8x8_queue
        self.d=display8x8(clk=cfg.clock8X8_pin, dio=cfg.data8x8_pin, bright=cfg.brightness8x8)
        self.question_mark = get_8x8_matrix("?")
        self.turn_off = get_8x8_matrix("all_off")
        self.d.write(self.turn_off)

    async def write(self, topic_list):
        print("do_8x8_list.write", topic_list)
        # first convert to 8x8
        char_matrix = []
        for topic in topic_list:
            if isinstance(topic, str):
                # parse topic get letter
                try:
                    ident = topic.split("/")[2]
                except:
                    ident = topic
                #print("do_8x8_list look up", ident)
                char_matrix.append(get_8x8_matrix(ident))
            else:
                char_matrix.append(self.question_mark)  # error
        await asyncio.sleep(0)
        while True: # displays letters until another message arrives
            for char8x8 in char_matrix:
                self.d.write(char8x8)
                await asyncio.sleep(0.5)
                self.d.write(self.turn_off)
                await asyncio.sleep(0.2)
            if not self.led_8x8_queue.empty():  # this loops until another msg availble
                break
            await asyncio.sleep(1)

#  asyncio task to display information
async def led_8x8_display(led_8x8_queue):
    # wait for an error
    error_code = 0
    next_code = 0
    list8x8 = do_8x8_list(led_8x8_queue)
    async for msg_list,  in led_8x8_queue:
        while not led_8x8_queue.empty(): # flush the queue, use last item
            async for msg_list, in led_8x8_queue:
                break
        print("led_8x8_display [%s] type [%s]" % (msg_list, type(msg_list)))
        #if isinstance(msg_list, list): # a list of strings to display on 8x8 led matrix
        await list8x8.write(msg_list)
        #else:
            #await list8x8.write(["?",])

def make_email_body():
    global current_watched_sensors
    body = 'name = "%s"\n' %  (cfg.cluster_id,)
    for topic in current_watched_sensors:
        name = topic.split("/")[2]
        try:
            parts = name.split(" ",1)
            if len(parts) == 1:
                parts.append("")
        except:
            parts = [name, ""]
        body += '%s - %s - state = %s\n' % (parts[0], parts[1], "FALSE / OPEN / POWERED DOWN" if current_watched_sensors[topic][PUBLISH_CYCLES_WITHOUT_A_MESSAGE] > cfg.other_message_threshold else "True / Closed / Powered Up")
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

async def up_so_subscribe(client, led_8x8_queue, single_led_queue):
    wild_topic = wildcard_subscribe.topic()
    while True:
        await client.up.wait()
        client.up.clear()
        print('doing subscribes', wild_topic)
        led_8x8_queue.put(("all_off",))
        single_led_queue.put("all_off")
        await client.subscribe(wildcard_subscribe.topic())
        print("emailing startup")
        await send_email("Starting", boilerplate)

async def down_report_outage(client, led_8x8_queue, single_led_queue):
    while True:
        await client.down.wait()
        client.down.clear()
        print('got outage')
        led_8x8_queue.put(("wifi",))
        single_led_queue.put("outage")

async def check_for_down_sensors(led_8x8_queue, single_led_queue):
    global current_watched_sensors
    should_we_turn_on_led = False
    need_email = 0
    sensor_down = []
    for sensor in  current_watched_sensors:
        #print("main sensor[%s][%s]" % (sensor, current_watched_sensors[sensor]))
        if current_watched_sensors[sensor][MESSAGE_THIS_CYCLE] == False:  # no message this cycle
            if (current_watched_sensors[sensor][PUBLISH_CYCLES_WITHOUT_A_MESSAGE] > cfg.other_message_threshold):
                sensor_down.append(sensor)
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
        single_led_queue.put("sensor_down")
    else:
        led_8x8_queue.put(("all_off",))
        single_led_queue.put("all_off")
    if need_email:
        await send_email("Power Outage(s)", make_email_body(), cluster_id_only=True)

async def main():
    global led
    print_flash_usage()
    for topic in cfg.hard_tracked_topics: # "hard" tracked topics are monitored from boot,  "soft" only after a publish
        add_current_watched_sensors(topic)
    led_8x8_queue = MsgQueue(20)
    single_led_queue = MsgQueue(20)
    # Local configuration, "config" came from mqtt_as
    print("wifi ssid[%s] pw[%s]" % (cfg.ssid, cfg.wifi_password,))
    config['ssid'] = cfg.ssid
    config['wifi_pw'] = cfg.wifi_password
    config['server'] = cfg.broker
    config["user"] = cfg.user
    config["password"] = cfg.password
    config["ssl"] = True
    config["ssl_params"] = {'server_hostname': cfg.broker}
    config["queue_len"] = 10  # Use event interface with default queue size
    config["response_time"] = 30

    MQTTClient.DEBUG = True  # Optional: print diagnostic messages
    client = MQTTClient(config)

    # led = alert_handler.alert_handler(cfg.led_gpio, None, onboard_led_pin=cfg.onboard_led_gpio)
    led_8x8_queue.put(["boot1","boot2",])
    single_led_queue.put("boot")
    sw = switch.switch(cfg.switch_gpio, client)
    print("creating asyncio tasks")
    asyncio.create_task(led_8x8_display(led_8x8_queue))
    asyncio.create_task(do_single_led(single_led_queue))
    await asyncio.sleep(2)
    asyncio.create_task(raw_messages(client, led_8x8_queue, single_led_queue))
    asyncio.create_task(up_so_subscribe(client, led_8x8_queue, single_led_queue))
    asyncio.create_task(down_report_outage(client, led_8x8_queue, single_led_queue))
    #
    # make first connection
    # mqtt_as requires a good connection to the broker/server at startup
    # it recovers and notifies automaticly
    #
    while True:
        # Even know mqtt_as automaticly reconnects an initial connection is required
        try:
            await client.connect()
        except Exception as e:
            print("connection problem [", e,);
            try:
                x=client._addr
                print("we have ip address broker not connecting", client._addr)
                led_8x8_queue.put(("broker",)) # report 3 flashes
                single_led_queue.put("broker")
            except:
                print("wifi failed no ip address")
                led_8x8_queue.put(("wifi",))  # report 2 flashes
                single_led_queue.put("wifi")
            await asyncio.sleep(10)
        else:
            print("ip address", client._addr)
            break
    led_8x8_queue.put(("all_off",))
    single_led_queue.put("all_off")
    switch_detected_power = 1 if cfg.switch_type == "NO" else 0  # NO Normaly Open
    while True:  # Main loop checking to see of other has published
        # first publish alive status
        if cfg.monitor_only == True: # we don't publish or get tracked
            pass  
        else:
            sw_value = sw.test()
            print("switch = %s switch_detected_power %s" % (sw_value, switch_detected_power))
            if (cfg.switch == True and sw.test() != switch_detected_power):
                await client.publish(cfg.publish, "down")
            else:
                print("publishing powered up message")
                await client.publish(cfg.publish, "up")
        # i=0
        
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

