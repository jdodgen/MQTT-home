# MIT license copyright 2025 Jim Dodgen
# Power Change Notifier
# No server (except for the MQTT Broker)
# All sensor run the same code and monitor the other sensors
# Universal version allowing unlimited sensors
# typically monitoring utility power and standby power
# turning on a LED and sending emails
# also publishes status
#
VERSION = (0, 3, 0)
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

# other_status = []
# for dev in cfg.devices_we_subscribe_to:
    # print("subscribing to:", dev)
    # other_status.append(feature_power.feature(cfg.cluster_id+"/"+dev, subscribe=True))

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

no_broker_msg ='''Could not connect to broker:
[%s]
retrying ...
''' % (cfg.broker,)
print(no_broker_msg)

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
            print("our id", id)
            smtp.write("CC: %s\nSubject:[PCN %s] %s\n\n%s\n" % (cfg.cc_string, id, subject, body,))
            smtp.send()
            smtp.quit()
        except Exception as e:
            print("email failed", body, e)

#
current_watched_sensors = {} # GLOBAL

#
def add_current_watched_sensors(topic):
    current_watched_sensors[topic] = {"got_other_message": False,
                                            "have_we_sent_power_is_down_email": False,
                                            "publish_cycles_without_a_message": 0,
                                            "start_time": 0}

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
            #if (topic == dev.topic()):  # just getting the published message means utility outlet is powered, payload not important
            current_watched_sensors[topic]["got_other_message"] = True
            if current_watched_sensors[topic]["have_we_sent_power_is_down_email"]:
                current_watched_sensors[topic]["have_we_sent_power_is_down_email"] = False
                current_watched_sensors[topic]["publish_cycles_without_a_message"] = 0
                seconds = time.time() - current_watched_sensors[topic]["start_time"]
                hours = seconds/3600
                minutes = seconds/60
                restored_sensors +=  ("# Power restored to [%s]\n# Down, Minutes: %.f (Hours: %.1f)\n" %
                    (topic.split("/")[2], minutes, hours))
                current_watched_sensors[topic]["start_time"]=0
        if restored_sensors:
            await send_email("Power restored", restored_sensors+make_email_body())
    print("raw_messages exiting?")
# async def raw_messages(client,error_queue):  # Process all incoming messages
    # global led
    # global other_status
    # # loop on message queue
    # async for btopic, bmsg, retained in client.queue:
        # topic = btopic.decode('utf-8')
        # msg = bmsg.decode('utf-8')
        # print("callback [%s][%s] retained[%s]" % (topic, msg, retained,))
        # i=0
        # restored_sensors = ""
        # for dev in other_status:
            # if (topic == dev.topic()):  # just getting the published message means utility outlet is powered, payload not important
                # cfg.got_other_message[i] = True
                # if cfg.have_we_sent_power_is_down_email[i]:
                    # cfg.have_we_sent_power_is_down_email[i] = False
                    # cfg.publish_cycles_without_a_message[i] = 0
                    # seconds = time.time() - cfg.start_time[i]
                    # hours = seconds/3600
                    # minutes = seconds/60
                    # restored_sensors +=  ("# Power restored to [%s]\n# Down, Minutes: %.f (Hours: %.1f)\n" %
                        # (cfg.devices_we_subscribe_to[i], minutes, hours))
                    # cfg.start_time[i]=0
            # i += 1
        # if restored_sensors:
            # await send_email("Power restored", restored_sensors+make_email_body())
    # print("raw_messages exiting?")

# DEBUG: show RAM messages.
    async def _memory(self):
        import gc
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
    for topic in cfg.hard_tracked_topics: # hard tracked topics are monitored from boot soft only after a publish
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
        if monitor_only == False:
            await client.publish(our_status.topic(), our_status.payload_on())
        i=0
        down_sensors = 0
        any_start_times = 0
        print("\b[publish_check_loop]")
        # need to loop on current_watched_sensors[topic]["got_other_message"]
        # print("main current_watched_sensors", current_watched_sensors)
        for sensor in  current_watched_sensors:
            #print("main sensor[%s][%s]" % (sensor, current_watched_sensors[sensor]))
            if current_watched_sensors[sensor]["got_other_message"] == False:  # no message(s) this cycle
                if (current_watched_sensors[sensor]["publish_cycles_without_a_message"] > cfg.other_message_threshold):
                    if (current_watched_sensors[sensor]["start_time"] == 0):
                        if (not current_watched_sensors[sensor]["have_we_sent_power_is_down_email"]):
                            down_sensors += 1
                            current_watched_sensors[sensor]["have_we_sent_power_is_down_email"] = True
                            current_watched_sensors[sensor]["start_time"]= time.time()
                else:
                    current_watched_sensors[sensor]["publish_cycles_without_a_message"] += 1
            else:  # other message(s) have arrived
                current_watched_sensors[sensor]["got_other_message"] = False
                current_watched_sensors[sensor]["publish_cycles_without_a_message"] = 0
            i += 1
            if current_watched_sensors[sensor]["start_time"] > 0:
                any_start_times += 1
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
        # body += "[%s]%s\n" % (dev, "OFF" if cfg.publish_cycles_without_a_message[i] > cfg.other_message_threshold else "ON")
        body += ''' [sensor.%s]\n  desc = "%s"\n  on = %s\n''' % (parts[0], parts[1], "false  #\t\t<>>>> \""+name+"\" is OFF <<<<>" if current_watched_sensors[topic]["publish_cycles_without_a_message"] > cfg.other_message_threshold else "true # on")
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

