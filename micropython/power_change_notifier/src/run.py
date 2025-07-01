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

other_status = []
list_of_others = []   # use this to get msgs back during testing [our_status.topic(),]
for dev in cfg.devices_we_subscribe_to:
    print("subscribing to:", dev)
    other_status.append(feature_power.feature(cfg.cluster_id+"/"+dev, subscribe=True))
    list_of_others.append(feature_power.feature(cfg.cluster_id+"/"+dev, subscribe=True).topic())
print("list of others", list_of_others)
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
    global other_status
    print(".raw_messages")
    async for btopic, bmsg in queue:
        topic = btopic.decode('utf-8')
        msg = bmsg.decode('utf-8')
        print(".raw_messages [%s][%s]" % (topic, msg))
        #print("callback start_time(s)", cfg.start_time)
        i=0
        restored_sensors = ""
        for dev in other_status:
            if (topic == dev.topic()):  # just getting the published message means utility outlet is powered, payload not important
                cfg.got_other_message[i] = True
                if cfg.have_we_sent_power_is_down_email[i]:
                    cfg.have_we_sent_power_is_down_email[i] = False
                    cfg.publish_cycles_without_a_message[i] = 0
                    seconds = time.time() - cfg.start_time[i]
                    hours = seconds/3600
                    minutes = seconds/60
                    restored_sensors +=  ("# Power restored to [%s]\n# Down, Minutes: %.f (Hours: %.1f)\n" %
                        (cfg.devices_we_subscribe_to[i], minutes, hours))
                    cfg.start_time[i]=0
            i += 1
        if restored_sensors:
            await send_email("Power restored", restored_sensors+make_email_body())

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

'''async def problem_reporter(error_code, repeat=1):
    if error_code >  0:
        led.turn_off()
        await asyncio.sleep(2)
        x = 0
        while x < repeat:
            await led.async_flash(count=error_code, duration=0.4, ontime=0.4)
            x += 1
            await asyncio.sleep(1)
        await asyncio.sleep(2)'''

async def main():
    global other_status
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
            subscriptions =  list_of_others,  # list_of_topics,
            # publish_retains = retains,     #
            )
    asyncio.create_task(raw_messages(mqtt.queue)) # incoming messages
    asyncio.create_task(problem_reporter(mqtt.error_queue)) # errors
    #asyncio.create_task(mqtt.monitor_wifi())  # connects and reconnects as needed
    #asyncio.create_task(mqtt.process_incoming_messages())
    #await asyncio.sleep(1)
    print(".main connecting to broker")
    client = await mqtt.broker()  # first connection to the broker.
    print(".main client connected")
    await client.publish(our_status.topic(), "client connected")
    '''
    print("creating tasks")
    # these are needed for mqtt_as_lite
    # they run forever and fix connection problems
    asyncio.create_task(client.monitor_wifi())
    asyncio.create_task(client._handle_msg())
    asyncio.create_task(client.monitor_broker())

    # this pulls messages from the queue
    #asyncio.create_task(raw_messages(client))
    #
    #done above'''

    await mqtt.wifi_up.wait()
    print(".main emailing startup")
    # await send_email("Starting" % (cfg.cluster_id, cfg.publish),errors_msg)
    await send_email("Starting", boilerplate)
    #
    # now checking on the broker connect. It too long then email
    '''
    start_broker_connect = time.time()
    too_long = 60
    broker_not_up_send_email = False
    while True:
        elapse  = time.time() - start_broker_connect
        huh = client.broker_connected.is_set()
        #print("elapse", elapse, huh)
        if huh:
            break
        if elapse > too_long and not broker_not_up_send_email:
            broker_not_up_send_email = True
            print("email no broker")
            await send_email("broker not found", "broker at ["+cfg.broker+"] not found")
        await asyncio.sleep(1)

    await client.broker_connected.wait()
    if broker_not_up_send_email:
        await send_email("Connected", "Broker now connected")
    '''

    #resub_loop_count = 0
    while True:  # top loop checking to see of other has published
        #await asyncio.sleep(120)
        # await client.publish(our_status.topic(), our_status.payload_on())
        # await asyncio.sleep(120)
        # await asyncio.sleep(2)
        # await client.publish(our_status.topic(), our_status.payload_on())
        # await asyncio.sleep(2)
        await client.publish(our_status.topic(), our_status.payload_on())
        #await client.subscribe(wildcard_subscribe.topic())
        # continue
        i=0
        down_sensors = 0
        print(".main \b[publish_check_loop]")
        for stat in  cfg.got_other_message:
            if stat == False:  # no message(s) this cycle
                if (cfg.publish_cycles_without_a_message[i] > cfg.other_message_threshold):
                    if (cfg.start_time[i] == 0):
                        if (not cfg.have_we_sent_power_is_down_email[i]):
                            down_sensors += 1
                            cfg.have_we_sent_power_is_down_email[i]= True
                            cfg.start_time[i] = time.time()
                else:
                    cfg.publish_cycles_without_a_message[i] += 1
            else:  # other message(s) have arrived
                cfg.got_other_message[i] = False
                cfg.publish_cycles_without_a_message[i] = 0
            i += 1
        if any(cfg.start_time):
            print(".main turning led on")
            led.turn_on()
        else:
            led.turn_off()
        if down_sensors:
            await send_email("Power Outage(s)", make_email_body(), cluster_id_only=True)
        # if client.do_subscribes or cfg.subscribe_interval < resub_loop_count:
            # client.do_subscribes = False
            # resub_loop_count = 0
            # print("subscribing ", wildcard_subscribe.topic())
            # await client.subscribe(wildcard_subscribe.topic())
            # #for dev in other_status:
                # #await client.subscribe(dev.topic())
        # resub_loop_count += 1
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
