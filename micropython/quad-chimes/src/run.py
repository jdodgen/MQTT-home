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
VERSION = (0, 3, 4)
import umail
import alert_handler
from mqtt_as import MQTTClient, config
import feature_power # this stays, nice to know if it running a publish will be done every 30 seconds (check PCN for the standard)
import mqtt_hello
import alert_handler
import cfg
import time
import asyncio
import time
import os
import switch
from msgqueue import  MsgQueue

# quad-chimes  stuff
import feature_quad_chimes
import feature_button
import feature_three_chimes
import button
quad_chimes =    feature_quad_chimes.feature(cfg.name,         subscribe=True)
btn =          feature_button.feature(cfg.name,            publish=True)
pin_play_all      = machine.Pin(cfg.play_all_pin,     machine.Pin.OUT)
pin_ding_dong     = machine.Pin(cfg.ding_dong_pin,    machine.Pin.OUT)
pin_ding_ding     = machine.Pin(cfg.ding_ding_pin,    machine.Pin.OUT)
pin_west          = machine.Pin(cfg.westminster_pin,  machine.Pin.OUT)
pin_play_all.value(1)
pin_ding_dong.value(1)
pin_ding_ding.value(1)
pin_west.value(1)
# end of quad-chimes  stuff

#our_status = feature_power.feature(cfg.cluster_id+"/"+cfg.publish, publish=True)   # publisher
print("Our topic = [%s]" % (cfg.publish,))

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
            id = cfg.cluster_id if cluster_id_only else cfg.cluster_id+"/"+cfg.publish
            print("our id [%s]" % (id,))
            smtp.write("CC: %s\nSubject:[PCN %s] %s\n\n%s\n" % (cfg.cc_string, id, subject, body,))
            smtp.send()
            smtp.quit()
        except Exception as e:
            print("email failed", body, e)

async def raw_messages(client,error_queue):  # Process all incoming messages
    global led
    global current_watched_sensors
    # global other_status
    # loop on message queue
    async for btopic, bmsg, retained in client.queue:
        topic = btopic.decode('utf-8')
        msg = bmsg.decode('utf-8')
        print("callback [%s][%s] retained[%s]" % (topic, msg, retained,)
        # this spends a second on each chime
        if topic == ding_ding.topic():
            print("chiming ...ding_ding")
            pin_ding_ding.value(0)
            await asyncio.sleep(1)
            pin_ding_ding.value(1)
            print("... chimed")
        elif topic == ding_dong.topic():
            print("chiming ...ding_dong")
            pin_ding_dong.value(0)
            await asyncio.sleep(1)
            pin_ding_dong.value(1)
            print("... chimed")
        elif (topic == westminster.topic()):
            print("chiming ...westminster")
            pin_west.value(0)
            await asyncio.sleep(1)
            pin_west.value(1)
            print("... chimed")
        elif (topic == three_chimes.topic()):
            print("chiming ...play_all")
            pin_play_all.value(0)
            await asyncio.sleep(1)
            pin_play_all.value(1)
            print("... chimed")
        elif (topic == btn.topic() and default_chime):
            print("chiming ...default_chime")
            default_chime.value(0)
            await asyncio.sleep(1)
            default_chime.value(1)
            print("... chimed")
        elif (topic == mqtt_hello.hello_request_topic):
            print("callback hello_request")
            await say_hello(client)
        else:
             print("unknown message")
          # await send_email("Power restored", restored_sensors+make_email_body())
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

async def main():
    #global other_status
    # global our_status
    global led
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
    sw = switch.switch(cfg.switch_gpio, client)
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
    while True:
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


############ startup ###############
time.sleep(cfg.start_delay)
print("starting")
try:
    asyncio.run(main())
finally:
    pass
    #client.close()
print("exiting, should not get here")
