# MIT license copyright 2025 Jim Dodgen
# Universal version allowing unlimited sensors
#
import umail
import alert_handler
from mqtt_as_lite import MQTTClient, config, turn_on_prints
import feature_power 
import mqtt_hello
import alert_handler
import cfg
import time
import asyncio
import time

other_status = []
for dev in cfg.devices_we_subscribe_to:
    print("subscribing to:", dev)
    other_status.append(feature_power.feature(cfg.cluster_id+"/"+dev, subscribe=True))

wildcard_subscribe = feature_power.feature(cfg.cluster_id+"/+", subscribe=True) 
print(wildcard_subscribe.topic())

our_status    = feature_power.feature(cfg.cluster_id+"/"+cfg.publish, publish=True)   # publisher

turn_on_prints(True)

# ERRORS from mqtt_as_lite.py 
errors_msg = '''Starting up ...\nFor reference:
Flashing LED error codes
1 starting up
2 ERROR_AP_NOT_FOUND
3 ERROR_BAD_PASSWORD
4 ERROR_BROKER_LOOKUP_FAILED
5 ERROR_BROKER_CONNECT_FAILED

LED solid on, indicates an outage.
LED out, normal no outage
'''

no_broker_msg ='''Could not connect to broker:
[%s]
retrying ...
''' % (cfg.server,)
print(no_broker_msg)

# conditional print
xprint = print # copy print
def print(*args, **kwargs): # replace print
    #return # comment/uncomment to turn print on off
    # do whatever you want to do
    #xprint('statement before print')
    xprint("[run]", *args, **kwargs) # the copied real print

async def send_email(subject,body, id=cfg.cluster_id):
    if cfg.send_email:
        try:
            smtp = umail.SMTP('smtp.gmail.com', 465, ssl=True)
            smtp.login(cfg.gmail_user, cfg.gmail_password)
            smtp.to(cfg.send_messages_to, mail_from="notifygenerator@gmail.com")
            smtp.write("Subject:[PCN %s] %s\n\n%s\n" % (cfg.cluster_id, subject, body,))
            smtp.send()
            smtp.quit()
        except:
            print("email failed", body) 


async def raw_messages(client):  # Process all incoming messages 
    global led
    global other_status
    # loop on message queue
    async for btopic, bmsg, retained in client.queue:
        topic = btopic.decode('utf-8')
        msg = bmsg.decode('utf-8')
        print("callback [%s][%s] retained[%s]" % (topic, msg, retained,)) 
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
            await send_email("Power restored",restored_sensors+make_email_body()) 
     
    print("raw_messages exiting")

# DEBUG: show RAM messages.
    async def _memory(self):
        import gc
        while True:
            await asyncio.sleep(20)
            gc.collect()
            print("RAM free %d alloc %d" % (gc.mem_free(), gc.mem_alloc()))

     
async def problem_reporter(error_code, repeat=1):
    if error_code >  0:
        led.turn_off()
        await asyncio.sleep(2)
        x = 0
        while x < repeat:
            await led.async_flash(count=error_code, duration=0.4, ontime=0.4)
            x += 1
            await asyncio.sleep(1)
        await asyncio.sleep(2)      
        
async def main(client):
    global other_status
    global our_status
    global led
    
    led = alert_handler.alert_handler(cfg.led_gpio, None)
    led.turn_on()
    await asyncio.sleep(2)  # wakeup flash
    led.turn_off() 

    print("creating tasks")
    # these are needed for mqtt_as_lite
    # they run forever and fix connection problems
    asyncio.create_task(client.monitor_wifi())
    asyncio.create_task(client._handle_msg())
    asyncio.create_task(client.monitor_broker())
    # this pulls messages from the queue
    asyncio.create_task(raw_messages(client))
    # 
    await client.wifi_up.wait()
    print("emailing startup")
    # await send_email("[%s:%s] Starting" % (cfg.cluster_id, cfg.publish),errors_msg)
    await send_email("Starting ", errors_msg, id="%s:%s" % (cfg.cluster_id, cfg.publish), errors_msg)
    #
    # now checking on the broker connect. It too long then email
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
            await send_email("P monitor [%s:%s] broker not found" % (cfg.cluster_id, cfg.publish), "broker at ["+cfg.server+"] not found")
        await asyncio.sleep(1)
   
    await client.broker_connected.wait()
    if broker_not_up_send_email:
        await send_email("P monitor [%s:%s] broker connected" % (cfg.cluster_id, cfg.publish), "Broker now connected")
   

    resub_loop_count = 0
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
            await send_email("Power Outage(s)", make_email_body())
        if client.do_subscribes or cfg.subscribe_interval < resub_loop_count:
            client.do_subscribes = False
            resub_loop_count = 0
            print("subscribing ", wildcard_subscribe.topic())
            await client.subscribe(wildcard_subscribe.topic())
            #for dev in other_status:
                #await client.subscribe(dev.topic())
        resub_loop_count += 1  
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
# Local configuration, "config" came from mqtt_as
config['ssid'] = cfg.ssid  
config['wifi_pw'] = cfg.wifi_password
config['server'] = cfg.server 
config["queue_len"] = 1  # Use event interface with default queue size
config['problem_reporter'] = problem_reporter
config["response_time"] = 30

MQTTClient.DEBUG = True  # Optional: print diagnostic messages
client = MQTTClient(config)
try:
    asyncio.run(main(client))
finally:
    pass
    #client.close()
print("exiting, should not get here")
