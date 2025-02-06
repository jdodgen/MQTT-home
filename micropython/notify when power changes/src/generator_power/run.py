# MIT license copyright 2025 Jim Dodgen
# Generator side
#
import umail
import alert_handler
from mqtt_as import MQTTClient, config
import feature_power 
import mqtt_hello
import alert_handler
import cfg
import time
import uasyncio as asyncio   # version for micropython

# conditional print
xprint = print # copy print
def print(*args, **kwargs): # replace print
    #return # comment/uncomment to turn print on off
    # do whatever you want to do
    #xprint('statement before print')
    xprint("[run]", *args, **kwargs) # the copied real print

async def send_email(body):
  smtp = umail.SMTP('smtp.gmail.com', 465, ssl=True)
  smtp.login(cfg.gmail_user, cfg.gmail_password)
  smtp.to(cfg.send_messages_to)
  smtp.write("From: NotifyGenerator <notifygenerator@gmail.com>\n")
  smtp.write("Subject: Power Outage\n\n%s\n" % body)
  smtp.send()
  smtp.quit()

done = False
start_time = time.time()

async def raw_messages(client):  # Respond to all incoming messages 
    global led
    global done
    global utility_status
    global start_time

    # loop on message queue
    async for btopic, bmsg, retained in client.queue:
        topic = btopic.decode('utf-8')
        msg = bmsg.decode('utf-8')
        if done == True:
            time.sleep(60)
            break
        print("callback [%s][%s][%s]" % (topic, msg, retained,))
        if (topic == utility_status.topic()):  # just getting the published message means utility outlet is powered, payload not important
            done = True
            if (on_generator == True):
                seconds_on_generator = time.time() - start_time
                hours_on = seconds_on_generator/3600 
                await send_email("Power restored, Generator now off\nMinutes on Generator: %.1f\nHours on Generator:%.1f\nAverage cost to run: %.2f" % 
                        (seconds_on_generator/60, hours_on,hours_on * cfg.cost_to_run))
            else:
                await send_email("Short loss of utility power, generator not running")
            led.turn_off()
            await client.unsubscribe(utility_status.topic())
    led.turn_off()
    print("raw_messages exiting")

async def check_if_up(client):  # Respond to connectivity being (re)established
    global valve
    global valve_state
    while True:
        await client.up.wait()  # Wait on an Event
        client.up.clear()
        await client.subscribe(utility_status.topic())
        # who am I sends a MQTT_hello message
        mqtt_hello.send_hello(client, "generator_power_status", "When running publishes \"power on\" in a loop, quits in an hour after boot",
        generator_status.feature_json(),
        utility_status.feature_json())
        await client.publish(generator_status.topic(), generator_status.payload_on())  
                         
        # h = hello(cfg.valve_name, "motor valve controler, with feedback")
        # h.add_feature(valve.feature_json())
        # h.add_feature(valve_state.feature_json())
        # h.payload()
        # print("hello topic[%s] payload[%s]" % (h.topic(), h.payload()))
        # await client.publish(h.topic(), h.payload()) 

async def main(client):
    global utility_status
    global generator_status
    global on_generator
    global led
    
    utility_status  = feature_power.feature("utility_power_status", subscribe=True)
    generator_status  = feature_power.feature("generator_power_status", publish=True)  # subscribe default is False so this is a publish
    on_generator = False
    led = alert_handler.alert_handler(cfg.led_gpio, None)
    led.turn_on()
    while True:
        print("checking connection")
        try:
            await client.connect()
        except:
            pass
        else:
            break
    # these are loops and run forever
    asyncio.create_task(check_if_up(client))
    asyncio.create_task(raw_messages(client))
    await client.subscribe(utility_status.topic())
    print("waiting [%s] seconds to decide if on generator" % (cfg.number_of_seconds_to_wait,))    
    await asyncio.sleep(cfg.number_of_seconds_to_wait)
    if done == False:  # we have recieved a "utl" message before the time-out
        print("timed out, sending on generator sms/email(s)")
        on_generator = True
        await send_email("No utility power: Now on secondary power")
    while True: # loop forever
        await asyncio.sleep(1000)
        # waiting for subscribe to callback 

time.sleep(cfg.start_delay)
print("starting")
# Local configuration, "config" came from mqtt_as
config['ssid'] = cfg.ssid  
config['wifi_pw'] = cfg.wifi_password
config['server'] = cfg.server 
config["queue_len"] = 1  # Use event interface with default queue size

MQTTClient.DEBUG = True  # Optional: print diagnostic messages
client = MQTTClient(config)
try:
    asyncio.run(main(client))
finally:
    client.close()
print("example exiting")
