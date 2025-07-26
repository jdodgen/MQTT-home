# MIT license copyright 2025 Jim Dodgen
# Power Change Notifier
# requires only a MQTT Broker. Local or in the Cloud
# All sensor run the identical code, only "cfg.py" is different
# No real limit to the number of sensors. Only  CPU and memory. 
# typically application is monitoring utility power and standby (Generator) power
# It monotors and turns on a LED also sends emails. 
# It optionaly publishes status for others to follow
# This is a Simple IoT.
# For any sensor this is the most importaint thing. "am I alive"
# I am using this code as the starting point for other more complex IoT sensors
# example is adding a gpio line to detect a swich or button:
# So for a door, if it is "true" AND "alive" it can be trusted that it is open.
# if not you are worried 
#
VERSION = (0, 3, 4)
import umail
import alert_handler
from mqtt_as import MQTTClient, config
import feature_power
#import mqtt_hello
import alert_handler
import cfg
import time
import asyncio
import time
from msgqueue import  MsgQueue

wildcard_subscribe = feature_power.feature(cfg.cluster_id+"/+", subscribe=True)
print(wildcard_subscribe.topic())

our_status = feature_power.feature(cfg.cluster_id+"/"+cfg.publish, publish=True)   # publisher
print("our_status = [%s]" % (our_status))

# ERRORS
boilerplate = '''Starting up ...\nFor reference:
Flashing LED error codes
1 Hello, starting up
2 ERROR_AP_NOT_FOUND or
  ERROR_BAD_PASSWORD
3 ERROR_BROKER_LOOKUP_FAILED or
  ERROR_BROKER_CONNECT_FAILED
5 Runtime failure, re-connecting
LED solid on, indicates an outage.
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
            smtp.login(cfg.gmail_user, cfg.gmail_password)
            smtp.to(cfg.send_messages_to, mail_from=cfg.gmail_user)
            id = cfg.cluster_id if cluster_id_only else cfg.cluster_id+":"+cfg.publish
            print("our id [%s]" % (id,))
            smtp.write("CC: %s\nSubject:[PCN %s] %s\n\n%s\n" % (cfg.cc_string, id, subject, body,))
            smtp.send()
            smtp.quit()
        except Exception as e:
            print("email failed", body, e)

#
# current_watched_sensors[topic][SUB_TOPICS]
current_watched_sensors = {} # it is GLOBAL
# SUB_TOPICS
MESSAGE_THIS_CYCLE = "message_this_cycle"
HAVE_WE_SENT_POWER_IS_DOWN_EMAIL = "have_we_sent_power_is_down_email"
PUBLISH_CYCLES_WITHOUT_A_MESSAGE = "publish_cycles_without_a_message"
START_TIME = "start_time"
#
def add_current_watched_sensors(topic):
    current_watched_sensors[topic] = {
        MESSAGE_THIS_CYCLE: True,
        HAVE_WE_SENT_POWER_IS_DOWN_EMAIL: False,
        PUBLISH_CYCLES_WITHOUT_A_MESSAGE: 0,
        START_TIME: 0}
    
async def raw_messages(client,error_queue):  # Process all incoming messages
    global led
    global current_watched_sensors
    # global other_status
    # loop on message queue
    async for btopic, bmsg, retained in client.queue:
        topic = btopic.decode('utf-8')
        msg = bmsg.decode('utf-8')
        print("callback [%s][%s] retained[%s]" % (topic, msg, retained,))
        if topic == our_status.topic():  # It is me!
            # print("raw_messages bypassing", topic)
            continue
        i=0
        restored_sensors = ""
        if topic not in current_watched_sensors:
            add_current_watched_sensors(topic)
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
            await send_email("Power restored", restored_sensors+make_email_body())
    print("raw_messages exiting?")
    
    def print_flash_usage():
        stat = os.statvfs('/')
        total_size = stat[1] * stat[2]
        free_space = stat[0] * stat[3]
        used_space = total_size - free_space
        print("Total Flash: {:,} bytes".format(total_size))
        print("Used Flash: {:,} bytes".format(used_space))
        print("Free Flash: {:,} bytes".format(free_space)) 
        
# show PSRAM messages.
    async def _memory(self):
        import gc
        import os
        while True:
            await asyncio.sleep(20)
            gc.collect()
            print("RAM free %d alloc %d" % (gc.mem_free(), gc.mem_alloc()))
            
#  called with the ERRORS listed above
async def problem_reporter(error_queue):
    # wait for an error
    error_code = 0
    next_code = 0
    async for error_code, in error_queue:
        print(".problem_reporter", error_code)
        while not error_queue.empty(): # flush the queue, use last item
            async for error_code, in error_queue:
                break
        if error_code > 0:
            while True:
                await led.async_flash(count=error_code, duration=0.5, ontime=0.5)
                for _ in range(error_code):
                    print("!!! flash !!!")
                    await asyncio.sleep(0.5)
                print("!!! end flash !!!", error_code)
                await asyncio.sleep(1)
                next_code = -1
                while not error_queue.empty(): # flush the queue, use last item
                    print(".problem_reporter queue not empty")
                    async for next_code, in error_queue:
                        print(".problem_reporter loop2", next_code)
                        break
                print(".problem_reporter next_code", next_code)
                if next_code == error_code or next_code == -1:  # same or nothing new
                    continue
                else:
                    break

async def main():
    #global other_status
    global our_status
    global led
    global current_watched_sensors
    print_flash_usage()
    for topic in cfg.hard_tracked_topics: # "hard" tracked topics are monitored from boot,  "soft" only after a publish
        add_current_watched_sensors(topic)
    error_queue = MsgQueue(20)
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

    led = alert_handler.alert_handler(cfg.led_gpio, None,onboard_led_pin=cfg.onboard_led_gpio)
    led.turn_on()
    await asyncio.sleep(1)  # wakeup flash
    led.turn_off()

    print("creating asyncio tasks")
    asyncio.create_task(raw_messages(client, error_queue))
    asyncio.create_task(up_so_subscribe(client, error_queue))
    asyncio.create_task(problem_reporter(error_queue))
    asyncio.create_task(down_report_outage(client, error_queue))
    #
    # make first connection
    # mqtt_as requires a good connection to the broker/server at startup
    # it recovers and notifies automaticly
    #
    while True:
        try:
            await client.connect()
        except Exception as e:
            print("connection problem [", e,);
            try:
                x=client._addr
                print("we have ip address broker not connecting", client._addr)
                error_queue.put(3) # report 3
            except:
                print("wifi failed no ip address")
                error_queue.put(2) #
            await asyncio.sleep(10)
        else:
            print("ip address", client._addr)
            break
    while True:  # top loop checking to see of other has published
        if cfg.monitor_only == False:
            await client.publish(our_status.topic(), our_status.payload_on())
        i=0
        down_sensors = 0
        any_start_times = False
        print("\b[publish_check_loop]")
        # need to loop on current_watched_sensors[topic][MESSAGE_THIS_CYCLE]
        for sensor in  current_watched_sensors:
            #print("main sensor[%s][%s]" % (sensor, current_watched_sensors[sensor]))
            if current_watched_sensors[sensor][MESSAGE_THIS_CYCLE] == False:  # no message this cycle
                if (current_watched_sensors[sensor][PUBLISH_CYCLES_WITHOUT_A_MESSAGE] > cfg.other_message_threshold):
                    if (current_watched_sensors[sensor][START_TIME] == 0):
                        if (not current_watched_sensors[sensor][HAVE_WE_SENT_POWER_IS_DOWN_EMAIL]):
                            down_sensors += 1
                            current_watched_sensors[sensor][HAVE_WE_SENT_POWER_IS_DOWN_EMAIL] = True
                            current_watched_sensors[sensor][START_TIME]= time.time()
                else:
                    current_watched_sensors[sensor][PUBLISH_CYCLES_WITHOUT_A_MESSAGE] += 1
            else:  # messages for this topic have arrived 
                current_watched_sensors[sensor][MESSAGE_THIS_CYCLE] = False # set false here, set true in raw_messages
                current_watched_sensors[sensor][PUBLISH_CYCLES_WITHOUT_A_MESSAGE] = 0
            i += 1
            if current_watched_sensors[sensor][START_TIME] > 0:
                any_start_times = True
        if any_start_times:
            led.turn_on()
        else:
            led.turn_off()
        if down_sensors:
            await send_email("Power Outage(s)", make_email_body(), cluster_id_only=True)
        await asyncio.sleep(cfg.number_of_seconds_to_wait)

def make_email_body():
    body = '''\
[cluster]
 name = "%s"
[sensor]\n''' %  (cfg.cluster_id,)
    #i = 0
    for topic in current_watched_sensors:
        name = topic.split("/")[2]
        try:
            parts = name.split(" ",1)
            if len(parts) == 1:
                parts.append("")
        except:
            parts = [name, ""]
        body += ''' [sensor.%s]\n  desc = "%s"\n  on = %s\n''' % (parts[0], parts[1], "false  #\t\t<>>>> \""+name+"\" is OFF <<<<>" if current_watched_sensors[topic][PUBLISH_CYCLES_WITHOUT_A_MESSAGE] > cfg.other_message_threshold else "true # on")
        #i += 1
    name = our_status.topic().split("/")[2]
    try:
        parts = name.split(" ",1)
        if len(parts) == 1:
            parts.append("")
    except:
        parts = [name, ""]
    body += ''' [sensor.%s] # reporting sensor\n  desc = "%s"\n  on = true''' % (parts[0], parts[1],)
    print(body)
    return body

async def up_so_subscribe(client, error_queue):
    while True:
        await client.up.wait()
        client.up.clear()
        print('doing subscribes')
        error_queue.put(0)
        await client.subscribe(wildcard_subscribe.topic())
        print("emailing startup")
        await send_email("Starting", boilerplate)

async def down_report_outage(client, error_queue):
    while True:
        await client.down.wait()
        client.down.clear()
        print('got outage')
        error_queue.put(5)


############ startup ###############
time.sleep(cfg.start_delay)
print("starting")
try:
    asyncio.run(main())
finally:
    pass
    #client.close()
print("exiting, should not get here")

