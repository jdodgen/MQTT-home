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
import asyncio
import network

#network.hostname(cfg.host_name)
#print("I am", network.hostname())

other_status  = feature_power.feature(cfg.subscribe, subscribe=True)


our_status    = feature_power.feature(cfg.publish, publish=True) 


# from mqtt_as.py 
ERROR_OK = 0
ERROR_AP_NOT_FOUND = 2
ERROR_BAD_PASSWORD = 3
ERROR_BROKER_LOOKUP_FAILED = 4
ERROR_BROKER_CONNECT_FAILED =  5

# conditional print
xprint = print # copy print
def print(*args, **kwargs): # replace print
    #return # comment/uncomment to turn print on off
    # do whatever you want to do
    #xprint('statement before print')
    xprint("[run]", *args, **kwargs) # the copied real print

async def send_email(body):
    try:
        smtp = umail.SMTP('smtp.gmail.com', 465, ssl=True)
        smtp.login(cfg.gmail_user, cfg.gmail_password)
        smtp.to(cfg.send_messages_to)
        smtp.write("From: device [%s]\n" % (cfg.publish,))
        smtp.write("Subject: Power Outage\n\n%s\n" % body)
        smtp.send()
        smtp.quit()
    except:
        print("email failed", body) 

got_other_message = False
start_time = time.time()
have_we_sent_power_is_down_email = False

async def raw_messages(client):  # Process all incoming messages 
    global led
    global got_other_message
    global other_status
    global start_time
    global have_we_sent_power_is_down_email
    # loop on message queue
    async for btopic, bmsg, retained in client.queue:
        topic = btopic.decode('utf-8')
        msg = bmsg.decode('utf-8')
        print("callback [%s][%s] retained[%s]" % (topic, msg, retained,))        
        if (topic == other_status.topic()):  # just getting the published message means utility outlet is powered, payload not important
            got_other_message = True
            if have_we_sent_power_is_down_email:
                have_we_sent_power_is_down_email = False
                seconds_on_generator = time.time() - start_time
                hours = seconds_on_generator/3600 
                minutes = seconds_on_generator/60
                await send_email(
                    "Power restored to [%s]\nDown, Minutes: %.1f (Hours: %.1f)" %  
                                (cfg.subscribe, minutes, hours))

            
    print("raw_messages exiting")

async def check_if_up(client):  # Respond to connectivity being (re)established
    global valve
    global valve_state
    while True:
        await client.up.wait()  # Wait on an Event
        client.up.clear()
        await client.subscribe(other_status.topic())
        # who am I sends a MQTT_hello message
        await mqtt_hello.send_hello(client, "our_status", "When running publishes \"power on\" in a loop",
        our_status.get(),
        other_status.get())
        print("check_if_up pub gen status")
        await client.publish(our_status.topic(), our_status.payload_on())  
        
async def problem_reporter(error_code):
    if error_code >  0:
        led.turn_off()
        await asyncio.sleep(1)
        x = 0
        while x < 1:
            led.flash(count=error_code, duration=0.4, ontime=0.4)
            x += 1
            await asyncio.sleep(1)
        await asyncio.sleep(1)      
        
async def main(client):
    global other_status
    global our_status
    global got_other_message
    global led
    global have_we_sent_power_is_down_email
    
    other_is_running = False
    led = alert_handler.alert_handler(cfg.led_gpio, None)
    
    #while True:
    print("checking connection")
    while True:
        try:
            await client.initial_connect()
            break
        except:
            error_code = client.status()
            if error_code >  0:
                x = 0
                while x < 1:
                    led.flash(count=error_code, duration=0.4, ontime=0.4)
                    x += 1
                    time.sleep(1)
        time.sleep(1)
    # led.turn_on()
    # these are loops and run forever
    asyncio.create_task(check_if_up(client))
    asyncio.create_task(raw_messages(client))
    await client.subscribe(other_status.topic())
    # now starting up 
    print("waiting [%s] seconds for other to boot and publish" % (cfg.start_delay,))    
    await asyncio.sleep(cfg.start_delay)
    
    no_other_cnt = 0
    resub_loop_count = 0
    while True:  # top loop checking to see of other has published
        await client.publish(our_status.topic(), our_status.payload_on())  
        if got_other_message == False:  # no message(s) this cycle
            no_other_cnt += 1
            if (no_other_cnt > cfg.other_message_threshold):
                if (not have_we_sent_power_is_down_email):
                    await send_email("[%s]down: [%s]up" % (cfg.subscribe, cfg.publish))
                    have_we_sent_power_is_down_email = True
                    led.turn_on()
        else:  # other message(s) have arrived
            got_other_message = False   # got one, wait for another
            led.turn_off()
        if (cfg.subscribe_interval < resub_loop_count):
            resub_loop_count = 0
            await client.subscribe(other_status.topic())
        resub_loop_count += 1  
        await asyncio.sleep(cfg.number_of_seconds_to_wait)

############ startup ###############
time.sleep(cfg.start_delay)
print("starting")
# Local configuration, "config" came from mqtt_as
config['ssid'] = cfg.ssid  
config['wifi_pw'] = cfg.wifi_password
config['server'] = cfg.server 
config["queue_len"] = 1  # Use event interface with default queue size
config['problem_reporter'] = problem_reporter

MQTTClient.DEBUG = True  # Optional: print diagnostic messages
client = MQTTClient(config)
try:
    asyncio.run(main(client))
finally:
    client.close()
print("example exiting")
