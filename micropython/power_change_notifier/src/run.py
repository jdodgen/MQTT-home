# MIT license copyright 2025 Jim Dodgen
# powered up monitor
# Universal version allowing unlimited sensors
# typically monitoring utility power and standby power
# turning on a LED and sending emails
# also publishes status
#
import umail
import alert_handler
# from mqtt_as_lite import MQTTClient, config, turn_on_prints
from mqtt_support import mqtt_support
import feature_power
# import mqtt_hello
import cfg
import time
import asyncio
import time

our_status    = feature_power.feature(cfg.cluster_id+"/"+cfg.publish, publish=True)   # publisher
print(our_status.topic())

#other_device_features = []
#other_device_topics = []
other_device_topics = [our_status.topic(),] # use this to get echo msgs back during testing

for dev in cfg.devices_we_subscribe_to:
    print("subscribing to:", dev)
    #other_device_features.append(feature_power.feature(cfg.cluster_id+"/"+dev, subscribe=True))
    other_device_topics.append(feature_power.feature(cfg.cluster_id+"/"+dev, subscribe=True).topic())
print("list of others", other_device_topics)

wildcard_subscribe = feature_power.feature(cfg.cluster_id+"/+", subscribe=True)
print(wildcard_subscribe.topic())




# ERRORS from mqtt_as_lite.py
boilerplate = '''Starting up ...\nFor reference:
Flashing LED error codes
1 starting up
2 ERROR_AP_NOT_FOUND
3 ERROR_BAD_PASSWORD
4 ERROR_BROKER_CONNECT_FAILED
LED solid on, indicates an outage.
LED out, normal no outage
'''

no_broker_msg ='''Could not connect to broker:
[%s]
retrying ...
''' % (cfg.broker,)
# print(no_broker_msg)

#
# conditional formatted print replacement
# Use mostly during micropython debugging
# MIT License Copyright Jim Dodgen 2025
# if first string starts with a "." then the first word of the string is appended to the print_tag
# typically identifying the routine or class
# tipical print statement:  "print(".internal_name hellow world, 2025)
# typical print output: "[file_name.internal_name] hello world 2025"
# this needs to be pasted into your .py
#
print_tag = "run" # The python file name
do_prints = True  # Set to False in production
#
def turn_on_prints(flag):  # true or false
    global do_prints
    do_prints=flag
raw_print = print # copy print
def print(first, *args, **kwargs): # replace print
    global do_prints
    if do_prints:
        f=None
        if isinstance(first, str) and first[0] == ".":
            f = first.split(" ",1)
        else:
            f = ["",first]
        try:
            if len(f) > 1:
                raw_print("["+print_tag+f[0]+"]", f[1], *args, **kwargs) # the copied real print
            else:
                raw_print("["+print_tag+f[0]+"]", *args, **kwargs) # the copied real print
        except:
            raise ValueError("xprint problem ["+print_tag+"]")
# end of conditional formatted print replacement 2025
#

async def send_email(subject, body, cluster_id_only=False):
    if cfg.send_email:
        try:
            smtp = umail.SMTP('smtp.gmail.com', 465, ssl=True)
            smtp.login(cfg.gmail_user, cfg.gmail_password)
            smtp.to(cfg.send_messages_to, mail_from=cfg.gmail_user)
            id = cfg.cluster_id if cluster_id_only else cfg.cluster_id+":"+cfg.publish
            smtp.write("CC: %s\nSubject:[PCN %s] %s\n\n%s\n" % (cfg.cc_string, id, subject, body,))
            smtp.send()
            smtp.quit()
        except Exception as e:
            print("email failed", body, e)

async def raw_messages(queue):  # Process all incoming messages
    global led
    global other_device_topics
    print(".raw_messages")
    async for btopic, bmsg in queue:
        topic = btopic.decode('utf-8')
        msg = bmsg.decode('utf-8')
        print(".raw_messages [%s][%s]" % (topic, msg))
        #print("callback start_time(s)", cfg.start_time)
        i=0
        information_text = "" # only one email for many outages
        for device_topic in other_device_topics:
            if (topic == device_topic):  # just getting the published message means utility outlet is powered, payload not important
                print(".raw_messages matched one we watch")
                cfg.got_other_message[i] = True
                if cfg.have_we_sent_power_is_down_email[i]:
                    print(".raw_messages  have_we_sent_power_is_down_email true")
                    cfg.have_we_sent_power_is_down_email[i] = False
                    cfg.publish_cycles_without_a_message[i] = 0
                    seconds = time.time() - cfg.start_time[i]
                    hours = seconds/3600
                    minutes = seconds/60
                    information_text +=  ("# Power restored to [%s]\n# Down, Minutes: %.f (Hours: %.1f)\n" %
                                                    (cfg.devices_we_subscribe_to[i], minutes, hours))
                    cfg.start_time[i]=0
            i += 1
        if information_text:
            await send_email("Power restored", information_text+make_email_body())

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
                    await asyncio.sleep(1)
                print("!!! end flash !!!", error_code)
                await asyncio.sleep(2)
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
    global our_status
    global led

    led = alert_handler.alert_handler(cfg.led_gpio, None)
    led.turn_on()
    await asyncio.sleep(2)  # wakeup flash
    led.turn_off()
    list_of_topics = [wildcard_subscribe.topic(),]
    mqtt = mqtt_support(
            ssid=cfg.ssid,
            wifi_pw=cfg.wifi_password,
            broker=cfg.broker,
            broker_user=cfg.user,
            broker_password=cfg.password,
            subscriptions =  other_device_topics,  # list_of_topics,
            # publish_retains = retains,     # need to add hello introduction
            )
    asyncio.create_task(raw_messages(mqtt.queue)) # incoming messages
    asyncio.create_task(problem_reporter(mqtt.error_queue)) # error number

    print(".main connecting to broker")
    client = await mqtt.broker()  # first connection to the broker.
    print(".main client connected")
    await client.publish(our_status.topic(), "client connected")

    await mqtt.wifi_up.wait()
    print(".main emailing startup")
    # await send_email("Starting" % (cfg.cluster_id, cfg.publish),errors_msg)
    await send_email("Starting", boilerplate)

    #resub_loop_count = 0
    while True:  # top loop checking to see of other has published
        await client.publish(our_status.topic(), our_status.payload_on())
        i=0
        down_device_cnt = 0
        print(".main \b[publish_check_loop]")
        for stat in  cfg.got_other_message:
            if stat == False:  # no message(s) this cycle
                if (cfg.publish_cycles_without_a_message[i] > cfg.other_message_threshold):
                    if (cfg.start_time[i] == 0):
                        if (not cfg.have_we_sent_power_is_down_email[i]):
                            down_device_cnt += 1
                            cfg.have_we_sent_power_is_down_email[i]= True
                            cfg.start_time[i] = time.time()
                else:
                    cfg.publish_cycles_without_a_message[i] += 1
            else:  # other message(s) have arrived
                cfg.got_other_message[i] = False
                cfg.publish_cycles_without_a_message[i] = 0
            i += 1
        if any(cfg.start_time):  # any in start_time True?
            print(".main turning led on", cfg.start_time)
            led.turn_on()
        else:
            print(".main turning led off", cfg.start_time)
            led.turn_off()
        if down_device_cnt:
            await send_email("Power Outage(s)", make_email_body(), cluster_id_only=True)
        await asyncio.sleep(cfg.number_of_seconds_to_wait)

def make_email_body():
    body = '''\
[cluster]
 name = "%s"
[sensor]\n''' %  (cfg.cluster_id,)
    i = 0
    for dev in cfg.devices_we_subscribe_to:
        # body += "[%s]%s\n" % (dev, "OFF" if cfg.publish_cycles_without_a_message[i] > cfg.other_message_threshold else "ON")
        body += ''' [sensor.%d]\n  name = "%s"\n  on = %s\n''' % (i, dev, "false  #\t\t<b><>>>> \""+dev+"\" OFF <<<<></b>" if cfg.publish_cycles_without_a_message[i] > cfg.other_message_threshold else "true # on")
        i += 1
    body += ''' [sensor.%d]\n  name = "%s" # reporting sensor\n  on = true'''% (i, cfg.publish)
    print(body)
    return body

############ startup ###############
time.sleep(cfg.start_delay)
print("starting")
'''
# Local configuration, "config" came from mqtt_as
config['ssid'] = cfg.ssid
config['wifi_pw'] = cfg.wifi_password

config["queue_len"] = 1  # Use event interface with default queue size
config['problem_reporter'] = problem_reporter
config["response_time"] = 30
config["keepalive"] = 7200
config['server'] = cfg.broker
config["ssl"] = cfg.ssl   # true or false
config["ssl_params"] = {'server_hostname': cfg.broker,}
config["user"] = cfg.user
config["password"] = cfg.password

MQTTClient.DEBUG = True  # Optional: print diagnostic messages
client = MQTTClient(config)
'''
try:
    #asyncio.run(main(client))
    asyncio.run(main())
finally:
    pass
    #client.close()
print("exiting, should not get here")
