# MIT license copyright 2025 Jim Dodgen
# simple_emailer built off of Power Change Notifier
# accepts a payload with subject and body and emails to the cfg.py emails
# this version to develop into a framework 
#
# requires only a MQTT Broker. Local or in the Cloud
# All sensor run the identical code, only "cfg.py" is different
# No real limit to the number of sensors. Only  Typical CPU and memory limatations.
# The original application was monitoring utility power and standby (Generator) power
# now monitoring a cluster of things for both power and optionaly the "dry contact" state
# which could be a power state like a solar system or even if a door is open.  
# It monitors and turns on a single or 8x8 LED's and sends emails.
# It publishes status for others to follow, it can be just a listener.
# This is a Simple IoT and a basis for other sensor and action IoT's.
# For any sensor/action this is the most important thing. "am I alive"
# I am using this code as the starting point for other more complex IoT sensors
# example is a "dry_contact" switch option monitoring a gpio line to detect a swich or button:
#
VERSION = (1, 0, 1)
import umail
import ubinascii
import network
import gc
from mqtt_as import MQTTClient, config, MsgQueue
import feature_power
import cfg
import time
import asyncio
import time
import urequests
import pcn
client = None
xprint = print # copy print
def print(*args, **kwargs): # replace print
    #return # comment/uncomment to turn print on off
    xprint("[run]", *args, **kwargs) # the copied real print
    
async def download_image_data(url, led_8x8_queue, single_led_queue):
    global client
    gc.collect()
    try:
        response = urequests.get(url)
        if response.status_code == 200:
            image_data = response.content # Read the content as bytes
            response.close()
            print("image_data len", len(image_data));
            return image_data
        else:
            print("Failed to download image. Status code:", response.status_code)
            gc.collect()
            response.close()
            return None
    except Exception as e:
        gc.collect()
        print("Error during HTTP request:", e)
        wlan = network.WLAN(network.STA_IF)

        # Deactivate the interface
        wlan.active(False)
        print("WiFi interface deactivated")

        # Wait for a moment before reactivating
        await asyncio.sleep(2)

        # Reactivate and reconnect
        wlan.active(True)
        client = await pcn.make_first_connection(config, led_8x8_queue, single_led_queue)
        return None

async def send_email(found_match,  led_8x8_queue, single_led_queue, cluster_id_only=False):
    # if cfg.send_email:
    try:
        smtp = umail.SMTP('smtp.gmail.com', 465, ssl=True)
        await asyncio.sleep(0)
        smtp.login(cfg.gmail_user, cfg.gmail_password)
        await asyncio.sleep(0)
        smtp.to(found_match["to_list"], mail_from=cfg.gmail_user)
        id = cfg.cluster_id if cluster_id_only else cfg.pretty_name
        print("our id [%s]" % (id,))
        smtp.write("CC: %s\nSubject:%s %s\n" % (found_match["cc_string"], found_match["subject"], id))
        smtp.write("MIME-Version: 1.0\n")
        smtp.write("Content-Type: multipart/mixed; boundary=boundary_string\n\n")
        smtp.write("--boundary_string\n")
        smtp.write("Content-Type: text/plain; charset=\"utf-8\"\n\n")
        smtp.write(found_match["body"]+"\n\n")
        cnt=0
        for url in found_match["image_urls"]:
            cnt += 1
            try:
                image = await download_image_data(url, led_8x8_queue, single_led_queue)
            except Exception as e:
                 print("Exception download_image_data", e)
            if image:
                try:
                    encoded_image = ubinascii.b2a_base64(image).decode('utf-8')
                except Exception as e:
                    print("Exception ubinascii.b2a_base64", e)
                    smtp.write("--boundary_string\n")
                    smtp.write("Content-Type: text/plain; charset=\"utf-8\"\n\n")
                    smtp.write(">>> problem encoding [%s]\n" % (url,))
                else:
                    print("encoded_image len", len(encoded_image))
                    smtp.write("--boundary_string\n")
                    smtp.write("Content-Type: image/jpeg\n")
                    smtp.write("Content-Disposition: attachment; filename=\"image%s.jpg\"\n" % (cnt,))
                    smtp.write("Content-Transfer-Encoding: base64\n\n")
                    chunk_size = 100
                    for i in range(0, len(encoded_image), chunk_size):
                        smtp.write(encoded_image[i:i+chunk_size])
                        await asyncio.sleep(0)
                    smtp.write("\n")
                
            else:
                smtp.write("--boundary_string\n")
                smtp.write("Content-Type: text/plain; charset=\"utf-8\"\n\n")
                smtp.write(">>> problem downloading [%s]\n" % (url,))
                
        
        smtp.write("--boundary_string--\n")   # note the trailing -- last boundry
        
        await asyncio.sleep(0)
        smtp.send()
        await asyncio.sleep(0)
        smtp.quit()
    except Exception as e:
        print("email failed", e)

async def raw_messages(client,led_8x8_queue, single_led_queue):  # Process all incoming messages
    print("raw_messages starting")
    async for btopic, bmsg, retained in client.queue:
        topic = btopic.decode('utf-8')
        msg = bmsg.decode('utf-8')
        print("callback [%s][%s] retained[%s]" % (topic, msg, retained,))
        this_topic = cfg.topics.get(topic, None)
        if this_topic:  # just checking
            print("raw_messages this_topic:", this_topic)
            print("keys:",this_topic.keys())
            found_match = {}
            
            if msg in this_topic.keys():  
                found_match = this_topic[msg]
                print("raw_messages msg found")
            elif "AlL"  in this_topic.keys():  # this is gets all for mqtt topic ignoring payload
                found_match = this_topic["AlL"]
                print("raw_messages AlA found")
            if found_match:
                subject = found_match["subject"]
                body = found_match["body"]
                cc_string = found_match["cc_string"]
                image_urls = found_match["image_urls"]
                await send_email(found_match, led_8x8_queue, single_led_queue)
    print("raw_messages exiting?")

async def main():
    global led
    global client
    pcn.print_flash_usage()
    led_8x8_queue = MsgQueue(20)
    single_led_queue = MsgQueue(20)
    
    config['server'] = cfg.broker
    config["user"] = cfg.user
    config["password"] = cfg.password
    config["ssl"] = True
    config["ssl_params"] = {'server_hostname': cfg.broker}
    config["queue_len"] = 10  # Use event interface with default queue size
    config["response_time"] = 30

    MQTTClient.DEBUG = True  # Optional: print diagnostic messages

    led_8x8_queue.put([("boot1",False),(cfg.device_letter,False),("boot2",False),(cfg.device_letter,False),])
    single_led_queue.put("boot")
    # sw = switch.switch(cfg.switch_pin, client)
    print("creating asyncio tasks")
    asyncio.create_task(pcn.led_8x8_display(led_8x8_queue))
    asyncio.create_task(pcn.do_single_led(single_led_queue))
    await asyncio.sleep(2)
    #
    # make first connection
    #
    print("make first connection")
    client = await pcn.make_first_connection(config, led_8x8_queue, single_led_queue)
    print("conneted")
    #
    asyncio.create_task(raw_messages(client, led_8x8_queue, single_led_queue))
    asyncio.create_task(pcn.up_so_subscribe(client, led_8x8_queue, single_led_queue, cfg.topics.keys()))
    asyncio.create_task(pcn.down_report_outage(client, led_8x8_queue, single_led_queue))        
    led_8x8_queue.put([("all_off", False),("life", False)])
    single_led_queue.put("all_off")
    # switch_detected_power = 1 if cfg.switch_type == "NO" else 0  # NO Normaly Open
    while True:  # Main loop checking to see of other has published
        print("[publish_check_loop]")
        await client.publish(cfg.publish, "up")
        led_8x8_queue.put([("all_off", False),("life", False)])
        await asyncio.sleep(cfg.number_of_seconds_to_wait)

############ startup ###############
time.sleep(cfg.start_delay)
print("starting")
try:
    asyncio.run(main())
finally:
    pass
    #client.close()
print("exiting, should not get here")
