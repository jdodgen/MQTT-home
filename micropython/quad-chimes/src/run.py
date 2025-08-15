# MIT license copyright 2025 Jim Dodgen
# Power Change Notifier PCN used as the template for sensors and actuators
# dif this with the PCN original for updates
# requires only a MQTT Broker. Local or in the Cloud
# All sensor run the identical code, only "cfg.py" is different
# No real limit to the number of sensors. Only  CPU and memory.
# typically application is monitoring utility power and standby (Generator) power
# It monitors and turns on a LED also sends emails.
# It optionally publishes status for others to follow
# This is a Simple IoT.
# For any sensor this is the most important thing. "am I alive"
# I am using this code as the starting point for other more complex IoT sensors
# example is "switch" option monitoring a gpio line to detect a swich or button:
# quad_chimes is both a sensor, the button. An actuator which is doing one of the four chimes
#
VERSION = (0, 0, 1)
import umail
import alert_handler
from mqtt_as import MQTTClient, config
import feature_power # this stays, nice to know if it running a publish will be done every 30 seconds (check PCN for the standard)
import mqtt_hello
import alert_handler
import cfg
import time
import asyncio
import os
<<<<<<< HEAD
# import switch
from msgqueue import  MsgQueue
import machine
# quad-chimes  stuff
import feature_quad_chimes
# import feature_button
# import feature_three_chimes
import button

=======
from msgqueue import  MsgQueue

PCN_heart_beat = feature_power.feature(cfg.cluster_id,)

# app imports
# quad-chimes  stuff
import feature_quad_chimes
import feature_button
import button


quad_chimes =    feature_quad_chimes.feature(cfg.cluster_id,)
btn =          feature_button.feature(cfg.cluster_id,)

>>>>>>> 0f08b038b768efed5f7f330ab85d59035d6bf900
pin_play_all      = machine.Pin(cfg.play_all_pin,     machine.Pin.OUT)
pin_ding_dong     = machine.Pin(cfg.ding_dong_pin,    machine.Pin.OUT)
pin_ding_ding     = machine.Pin(cfg.ding_ding_pin,    machine.Pin.OUT)
pin_west          = machine.Pin(cfg.westminster_pin,  machine.Pin.OUT)
pin_play_all.value(1)
pin_ding_dong.value(1)
pin_ding_ding.value(1)
pin_west.value(1)
# end of quad-chimes  stuff

<<<<<<< HEAD
#our_status = feature_power.feature(cfg.cluster_id+"/"+cfg.publish, publish=True)   # publisher
=======

print("Our topic = [%s]" % (cfg.publish,))
>>>>>>> 0f08b038b768efed5f7f330ab85d59035d6bf900

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

subject="button pressed"
body="Quad chimes button pressed"
async def send_email(subject, body, cluster_id_only=False):
    if cfg.send_email:
        try:
            smtp = umail.SMTP('smtp.gmail.com', 465, ssl=True)
            smtp.login(cfg.gmail_user, cfg.gmail_password)
            smtp.to(cfg.send_messages_to, mail_from=cfg.gmail_user)
<<<<<<< HEAD
            id = cfg.cluster_id+"/"+cfg.location
            print("our id [%s]" % (id,))
            smtp.write("CC: %s\nSubject:[quad_chimes %s] %s\n\n%s\n" % (cfg.cc_string, id, subject, body,))
            smtp.send()
            smtp.quit()
        except Exception as e:
            print("email failed", e)

=======
            print("our id [%s]" % (cfg.cluster_id,))
            smtp.write("CC: %s\nSubject:[PCN %s] %s\n\n%s\n" % (cfg.cc_string, cfg.cluster_id, subject, body,))
            smtp.send()
            smtp.quit()
        except Exception as e:
            print("email failed", body, e)
            
hardcoded_generic_description ="Four different chimes and a button" 
async def say_hello(client):
 # who am I sends a hello 
    print("say_hello: sending hello")
    await mqtt_hello.send_hello(client, cfg.name, 
                        hardcoded_generic_description, 
                        quad_chimes.get(),
                        three_chimes.get(),
                        btn.get(), 
                        )
>>>>>>> 0f08b038b768efed5f7f330ab85d59035d6bf900
async def raw_messages(client,error_queue):  # Process all incoming messages
    global led
    global current_watched_sensors
    quad_chimes =    feature_quad_chimes.feature(cfg.cluster_id)
    async for btopic, bmsg, retained in client.queue:
        topic = btopic.decode('utf-8')
        msg = bmsg.decode('utf-8')
        print("callback [%s][%s] retained[%s]" % (topic, msg, retained,))
        # this spends a second on each chime
        if (topic == mqtt_hello.hello_request_topic):
            print("callback hello_request")
            await say_hello(client)
        else:
            if (msg == quad_chimes.payload_ding_ding()):
                print("chiming ...ding_ding", end="")
                pin_ding_ding.value(0)
                await asyncio.sleep(cfg.time_to_trigger)
                pin_ding_ding.value(1)
                print("... chimed")
            elif (msg == quad_chimes.payload_ding_dong()):
                print("chiming ...ding_dong", end="")
                pin_ding_dong.value(0)
                await asyncio.sleep(cfg.time_to_trigger)
                pin_ding_dong.value(1)
                print("... chimed")
            elif (msg == quad_chimes.payload_westminster()):
                print("chiming ...westminster", end="")
                pin_west.value(0)
                await asyncio.sleep(cfg.time_to_trigger)
                pin_west.value(1)
                print("... chimed")
            elif (msg == quad_chimes.payload_three_chimes()):
                print("chiming ...play_all", end="")
                pin_play_all.value(0)
                await asyncio.sleep(cfg.time_to_trigger)
                pin_play_all.value(1)
                print("... chimed")
            else:
                print("unknown payload", msg)
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
        print("RAM free %d alloc %d" % (gc.mem_free(), gc.mem_alloc(), ))

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
        body += ''' [sensor.%s]\n  desc = "%s"\n  state = %s\n''' % (parts[0], parts[1], "false  #\t\t<>>>> \""+name+"\" is OFF <<<<>" if current_watched_sensors[topic][PUBLISH_CYCLES_WITHOUT_A_MESSAGE] > cfg.other_message_threshold else "true # on")
        #i += 1
    name = cfg.publish.split("/")[2]
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
    wildcard_subscribe = feature_quad_chimes.feature(cfg.cluster_id, location="+")
    wild_topic = wildcard_subscribe.topic()
    print(wild_topic)
    while True:
        await client.up.wait()
        client.up.clear()
        print('doing subscribes', wild_topic)
        error_queue.put(0)
        await client.subscribe(wild_topic)
        print("emailing startup")
        await send_email("Starting", "")

async def down_report_outage(client, error_queue):
    while True:
        await client.down.wait()
        client.down.clear()
        print('got outage')
        error_queue.put(5)

async def main():
    global led
    button_press = button.button(cfg.button_pin)
    print_flash_usage()
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

    led = alert_handler.alert_handler(cfg.led_gpio, None, onboard_led_pin=cfg.onboard_led_gpio)
    led.turn_on()
    await asyncio.sleep(1)  # wakeup flash
    led.turn_off()
    button_press = button.button(cfg.button_pin, client)
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
    #
    # connected now and forever so int to the loop
    #
<<<<<<< HEAD
    time_last_power_publish = 0
    while True:
        now = time.time()
        if (time_last_power_publish + cfg.number_of_seconds_to_wait < now):
            time_last_power_publish=now
            await client.publish(cfg.PCN_publish_power, "power_detected")
        if (button_press.test() == 0):
            print("button pressed")
            await client.publish(cfg.publish_button, cfg.publish_button_payload)
            await asyncio.sleep(1) # debounce pause
        await asyncio.sleep(0.1)
=======
    time_last_power_publish = 0;
    while True:
        now = time.time()
        if (time_last_power_publish + cfg.number_of_seconds_to_wait < now:
            time_last_power_publish=now
            await client.publish(PCN_heart_beat.topic(), "power_detected")
        if (button_press.test() == 0):
            await client.publish(btn.topic(), btn.payload_on())
            print("button pressed")
            if cfg.echo_chime:
                await client.publish(cfg.echo_chime_topic, cfg.chime)
        await asyncio.sleep(0.1)

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
        body += ''' [sensor.%s]\n  desc = "%s"\n  state = %s\n''' % (parts[0], parts[1], "false  #\t\t<>>>> \""+name+"\" is OFF <<<<>" if current_watched_sensors[topic][PUBLISH_CYCLES_WITHOUT_A_MESSAGE] > cfg.other_message_threshold else "true # on")
        #i += 1
    name = cfg.publish.split("/")[2]
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
        error_queue.put(0)
        print('doing subscribes')
        await client.subscribe(ding_ding.topic())
        await client.subscribe(ding_dong.topic())
        await client.subscribe(westminster.topic())
        await client.subscribe(three_chimes.topic())

async def down_report_outage(client, error_queue):
    while True:
        await client.down.wait()
        client.down.clear()
        print('got outage')
        error_queue.put(5)

>>>>>>> 0f08b038b768efed5f7f330ab85d59035d6bf900

############ startup ###############
time.sleep(cfg.start_delay)
print("starting")
try:
    asyncio.run(main())
finally:
    pass
    #client.close()
print("exiting, should not get here")
