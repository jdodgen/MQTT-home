# MIT license copyright 2025 Jim Dodgen
# powered up monitor
# Universal version allowing unlimited sensors
# typically monitoring utility power and standby power
# turning on a LED and sending emails
# also publishes status
#
VERSION = (0, 2, 2)
import umail
import alert_handler
from mqtt_as import MQTTClient, config  #,  turn_on_prints
import feature_power
#import mqtt_hello
import alert_handler
import cfg
import time
import asyncio
import time
from msgqueue import  MsgQueue

other_status = []
for dev in cfg.devices_we_subscribe_to:
    print("subscribing to:", dev)
    other_status.append(feature_power.feature(cfg.cluster_id+"/"+dev, subscribe=True))

wildcard_subscribe = feature_power.feature(cfg.cluster_id+"/+", subscribe=True)
print(wildcard_subscribe.topic())

our_status    = feature_power.feature(cfg.cluster_id+"/"+cfg.publish, publish=True)   # publisher


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

async def raw_messages(client,error_queue):  # Process all incoming messages
    global led
    global other_status
    # loop on message queue
    async for btopic, bmsg, retained in client.queue:
        topic = btopic.decode('utf-8')
        msg = bmsg.decode('utf-8')
        print("callback [%s][%s] retained[%s]" % (topic, msg, retained,))
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
    print("raw_messages exiting?")

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
    global other_status
    global our_status
    global led
    error_queue = MsgQueue(20)
    # Local configuration, "config" came from mqtt_as
    config['ssid'] = cfg.ssid
    config['wifi_pw'] = cfg.wifi_password
    config['server'] = cfg.broker
    config["user"] = cfg.user
    config["password"] = cfg.password
    config["ssl"] = True
    config["ssl_params"] = {'server_hostname': cfg.broker}
    config["queue_len"] = 10  # Use event interface with default queue size
    #config['problem_reporter'] = problem_reporter
    config["response_time"] = 30
    MQTTClient.DEBUG = True  # Optional: print diagnostic messages
    client = MQTTClient(config)

    led = alert_handler.alert_handler(cfg.led_gpio, None)
    led.turn_on()
    await asyncio.sleep(2)  # wakeup flash
    led.turn_off()

    print("creating tasks")
    asyncio.create_task(raw_messages(client,error_queue))
    asyncio.create_task(up_so_subscribe(client,error_queue))
    asyncio.create_task(problem_reporter(error_queue))
    asyncio.create_task(down_report_outage(client,error_queue))
    #


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
        await client.publish(our_status.topic(), our_status.payload_on())
        i=0
        down_sensors = 0
        print("\b[publish_check_loop]")
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
    i = 0
    for dev in cfg.devices_we_subscribe_to:
        # body += "[%s]%s\n" % (dev, "OFF" if cfg.publish_cycles_without_a_message[i] > cfg.other_message_threshold else "ON")
        body += ''' [sensor.%d]\n  name = "%s"\n  on = %s\n''' % (i, dev, "false  #\t\t<>>>> \""+dev+"\" OFF <<<<>" if cfg.publish_cycles_without_a_message[i] > cfg.other_message_threshold else "true # on")
        i += 1
    body += ''' [sensor.%d]\n  name = "%s" # reporting sensor\n  on = true'''% (i, cfg.publish)
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

