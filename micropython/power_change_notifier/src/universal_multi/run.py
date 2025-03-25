# MIT license copyright 2025 Jim Dodgen
# Universal version allowing many sensors
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

other_status = []
for dev in cfg.devices_we_subscribe_to:
    print("subscribing to:", dev)
    other_status.append(feature_power.feature(cfg.cluster_id+"/"+dev, subscribe=True))

our_status    = feature_power.feature(cfg.cluster_id+"/"+cfg.publish, publish=True)   # publisher


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

async def send_email(subject,body):
    try:
        smtp = umail.SMTP('smtp.gmail.com', 465, ssl=True)
        smtp.login(cfg.gmail_user, cfg.gmail_password)
        smtp.to(cfg.send_messages_to, mail_from="notifygenerator@gmail.com")
        smtp.write("From: Sensor [%s:%s] Reporting\n" % (cfg.cluster_id, cfg.publish,))
        smtp.write("Subject: %s\n\n%s\n" % (subject,body))
        smtp.send()
        smtp.quit()
    except:
        print("email failed", body) 

#got_other_message = False
#start_time = 0
#have_we_sent_power_is_down_email = False

async def raw_messages(client):  # Process all incoming messages 
    global led
    global other_status
    # loop on message queue
    async for btopic, bmsg, retained in client.queue:
        topic = btopic.decode('utf-8')
        msg = bmsg.decode('utf-8')
        print("callback [%s][%s] retained[%s]" % (topic, msg, retained,)) 
        print("callback start_time(s)", cfg.start_time)
        i=0
        restored_sensors = ""
        for dev in other_status:      
            if (topic == dev.topic()):  # just getting the published message means utility outlet is powered, payload not important
                cfg.got_other_message[i] = True
                if cfg.have_we_sent_power_is_down_email[i]:
                    cfg.have_we_sent_power_is_down_email[i] = False
                    seconds = time.time() - cfg.start_time[i]
                    hours = seconds/3600
                    minutes = seconds/60
                    restored_sensors +=  "Power restored to [%s]\nDown, Minutes: %.f (Hours: %.1f)" %  
                                    (cfg.devices_we_subscribe_to[i], minutes, hours)
                    cfg.start_time[i]=0
            i += 1
        if restored_sensors: await send_email("Power restored",restored_sensors) 
     
    print("raw_messages exiting")

async def check_if_up(client):  # Respond to connectivity being (re)established
    #global valve
    #global valve_state
    global other_status
    global our_status
    while True:
        await client.up.wait()  # Wait on an Event
        client.up.clear()
        for dev in other_status:
            await client.subscribe(dev.topic())
        # who am I sends a MQTT_hello message
        gets=[]
        for dev in other_status:
            gets.append(dev.get())
            print(dev.topic())

        await mqtt_hello.send_hello(client, "our_status", "When running publishes \"power on\" in a loop",
        our_status.get(),
        gets
        )
        print("check_if_up publish our_status")
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
    global led
    
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
    for dev in other_status:
        await client.subscribe(dev.topic())

    ###  now starting up 
    print("waiting [%s] seconds for other to boot and publish" % (cfg.start_delay,))    
    await asyncio.sleep(cfg.start_delay)
    
    #publish_cycles_without_a_message = 0
    resub_loop_count = 0
    while True:  # top loop checking to see of other has published
        await client.publish(our_status.topic(), our_status.payload_on()) 
        i=0
        down_sensors = ""
        for stat in  cfg.got_other_message:
            if stat == False:  # no message(s) this cycle
                cfg.publish_cycles_without_a_message[i] += 1
                if (cfg.publish_cycles_without_a_message[i] > cfg.other_message_threshold and cfg.start_time[i] == 0):
                    if (not cfg.have_we_sent_power_is_down_email[i]):
                        down_sensors += cfg.devices_we_subscribe_to[i]+", "
                        cfg.have_we_sent_power_is_down_email[i]= True
                        cfg.start_time[i] = time.time()
            else:  # other message(s) have arrived
                cfg.got_other_message[i] = False 
                cfg.publish_cycles_without_a_message[i] = 0
            i += 1
        if any(cfg.start_time):
            led.turn_on() 
        else:
            led.turn_off()
        if down_sensors: await send_email("Power Outage","NOTICE [%s] is/are OFF\n%s" % (down_sensors, make_email_body()))
        if (cfg.subscribe_interval < resub_loop_count):
            resub_loop_count = 0
            for dev in other_status:
                await client.subscribe(dev.topic())
        resub_loop_count += 1  
        await asyncio.sleep(cfg.number_of_seconds_to_wait)

def make_email_body(): 
    body = "Sensors status:\n"
    i = 0
    for dev in cfg.devices_we_subscribe_to:
         
        body += "[%s]%s\n" % (dev, "OFF" if cfg.publish_cycles_without_a_message[i] > cfg.other_message_threshold else "ON")
        i += 1
    print(body)
    return body
        
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
print("exiting, should not get here")
