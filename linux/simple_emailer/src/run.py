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
#import mail
import smtplib
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import ssl
import binascii
#import network
import multiprocessing
from mqtt_manager import mqtt_manager
#import feature_power
import cfg
import time
import requests

#client = None
xprint = print # copy print
def print(*args, **kwargs): # replace print
    #return # comment/uncomment to turn print on off
    xprint("[run]", *args, **kwargs) # the copied real print
    
def download_image_data(url):
    print("download_image_data", url)
    try:
        if len(url) == 3:
            print("download_image_data doing auth[%s][%s]" % (url[1], url[2]))
            response = requests.get(url[0], auth=requests.auth.HTTPDigestAuth(url[1], url[2]))
        else:
            response = requests.get(url[0])
        if response.status_code == 200:
            image_data = response.content # Read the content as bytes
            response.close()
            print("image_data len", len(image_data));
            return image_data
        else:
            print("Failed to download image. Status code:", response.status_code)
            image_data = None
            response.close() 
            return None
    except Exception as e:
        image_data = None
        print("Error during HTTP request:", e)
        return None

# async def old_send_email(found_match,  led_8x8_queue, single_led_queue, cluster_id_only=False):
    # # if cfg.send_email:
    # try:
        # smtp = mail.SMTP('smtp.gmail.com', 465, ssl=True)
        # await asyncio.sleep(0)
        # smtp.login(cfg.gmail_user, cfg.gmail_password)
        # await asyncio.sleep(0)
        # smtp.to(found_match["to_list"], mail_from=cfg.gmail_user)
        # id = cfg.cluster_id if cluster_id_only else cfg.pretty_name
        # print("our id [%s]" % (id,))
        
        # smtp.write("CC: %s\nSubject:%s %s\n" % (found_match["cc_string"], found_match["subject"], id))
        # print("CC write")
        # smtp.write("MIME-Version: 1.0\n")
        # smtp.write("Content-Type: multipart/mixed; boundary=boundary_string\n\n")
        # print("Content-Type: multipart/mixed")
        # smtp.write("--boundary_string\n")
        # smtp.write("Content-Type: text/plain; charset=\"utf-8\"\n\n")
        # print("Content-Type: text/plain")
        # smtp.write(found_match["body"]+"\n\n")
        # cnt=0
        # for url in found_match["image_urls"]:
            # cnt += 1
            # try:
                # image = await download_image_data(url, led_8x8_queue, single_led_queue)
            # except Exception as e:
                 # print("Exception download_image_data", e)
            # if image:
                # try:
                    # encoded_image = binascii.b2a_base64(image).decode('utf-8')
                # except Exception as e:
                    # print("Exception binascii.b2a_base64", e)
                    # smtp.write("--boundary_string\n")
                    # smtp.write("Content-Type: text/plain; charset=\"utf-8\"\n\n")
                    # smtp.write(">>> problem encoding [%s]\n" % (url,))
                # else:
                    # print("encoded_image len", len(encoded_image))
                    # smtp.write("--boundary_string\n")
                    # smtp.write("Content-Type: image/jpeg\n")
                    # smtp.write("Content-Disposition: attachment; filename=\"image%s.jpg\"\n" % (cnt,))
                    # smtp.write("Content-Transfer-Encoding: base64\n\n")
                    # chunk_size = 1000
                    # for i in range(0, len(encoded_image), chunk_size):
                        # smtp.write(encoded_image[i:i+chunk_size])
                        # await asyncio.sleep(0)
                    # smtp.write("\n")
                
            # else:
                # smtp.write("--boundary_string\n")
                # smtp.write("Content-Type: text/plain; charset=\"utf-8\"\n\n")
                # smtp.write(">>> problem downloading [%s]\n" % (url,))
                
        
        # smtp.write("--boundary_string--\n")   # note the trailing -- last boundry
        
        # await asyncio.sleep(0)
        # smtp.send()
        # await asyncio.sleep(0)
        # smtp.quit()
    # except Exception as e:
        # print("email failed", e)
        
# def make_body(found_match, encoded_jpgs):
    # body = "MIME-Version: 1.0\n"+
    # "Content-Type: multipart/mixed; boundary=boundary_string\n\n"+
    # "--boundary_string\n"+
    # "Content-Type: text/plain; charset=\"utf-8\"\n\n")+
    # found_match["body"]+"\n\n"
    # cnt=0
    # for url, ejpg in encoded_jpgs:
        # cnt += 1
        # if ejpg:
            # body += "--boundary_string\n"+
            # "Content-Type: image/jpeg\n")+
            # "Content-Disposition: attachment; filename=\"image%s.jpg\"\n" % (cnt,)+
            # "Content-Transfer-Encoding: base64\n\n"
            # for i in range(0, len(ejpg), chunk_size):
                # try:
                    # smtp.write(ejpg[i:i+chunk_size])
                # except Exception as e:
                    # print("encoded write failed", e)
        # else:
            # smtp.write("--boundary_string\n")
            # smtp.write("Content-Type: text/plain; charset=\"utf-8\"\n\n")
            # smtp.write(">>> problem downloading [%s]\n" % (url,))
    # smtp.write("--boundary_string--\n")   # note the trailing -- last boundry
       
        
def send_email_task(image_q, cluster_id_only=False):
    print("send_email_task starting")
    chunk_size = 100
    while True:
        found_match, jpgs = image_q.get()
        #context = ssl.create_default_context()
        #email_body = make_body(found_match, encoded_jpgs)
        # msg.set_content(email_body)
        idd = cfg.cluster_id if cluster_id_only else cfg.pretty_name
        print("our id [%s]" % (id,))
        msg = MIMEMultipart()
        msg['Subject'] = found_match["subject"] # +" "+idd
        msg['From'] = cfg.gmail_user
        msg['To'] = found_match["cc_string"]
        msg['Cc'] = found_match["cc_string"]
        for url, jpg in jpgs:
            print("MIMEImage", url)
            msg_image = MIMEImage(jpg, "jpeg", name="")
            msg.attach(msg_image)
        smtp = smtplib.SMTP('smtp.gmail.com', 587)
        smtp.ehlo()
        smtp.starttls()
        smtp.login(cfg.gmail_user, cfg.gmail_password)
        smtp.send_message(msg)
        smtp.quit()
        
def sample_send_email_with_image(subject, body, image_path):
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = 'example@example.com'
    msg['To'] = 'recipient@example.com'
    msg.attach(MIMEText(body, 'html'))
    with open(image_path, 'rb') as img:
        msg_image = MIMEImage(img.read(), name=os.path.basename(image_path))
        msg.attach(msg_image)
    smtp = smtplib.SMTP('smtp.gmail.com', 465)
    smtp.ehlo()
    smtp.starttls()
    smtp.login(cfg.gmail_user, cfg.gmail_password)
    smtp.send_message(msg)
    smtp.quit()
        # try:
            # try:
                # smtp = mail.SMTP('smtp.gmail.com', 465, is_ssl=True)
            # except Exception as e:
                # print("mail.SMTP failed", e)
            # smtp.login(cfg.gmail_user, cfg.gmail_password)
            # smtp.to(found_match["to_list"], mail_from=cfg.gmail_user)
            
            # try:
                # smtp.write("CC: %s\nSubject:%s %s\n" % (found_match["cc_string"], found_match["subject"], id))
            # except Exception as e:
                # print("first write failed", e)
                        # smtp.send()
            # smtp.quit()
            # print("send_email_task end of loop")
        # except Exception as e:
            # print("email failed --- ", e)

def main():
    mqtt_q = multiprocessing.Queue(10)
    image_q = multiprocessing.Queue(10)
    emailer = multiprocessing.Process(target=send_email_task, args=(image_q,))
    emailer.start()
    client = mqtt_manager(mqtt_q)
    while True:
        print("main loop")
        topic, payload = mqtt_q.get()
        this_topic = cfg.topics.get(topic, None)
        if this_topic:  # just checking
            print("main this_topic:", this_topic)
            print("keys:",this_topic.keys())
            found_match = {}
            if payload in this_topic.keys():  
                found_match = this_topic[payload]
                print("main msg found")
            elif "AlL"  in this_topic.keys():  # this is gets all for mqtt topic ignoring payload
                found_match = this_topic["AlL"]
                print("main AlL found")
            if found_match:
                images = []
                image_urls = found_match["image_urls"]
                for url in image_urls:
                    try:
                        image = download_image_data(url)
                    except Exception as e:
                        print("Exception download_image_data", e)
                        image = None
                    else:
                        print("got image", url, type(image), image[:300])
                        # try:        
                            # encoded_image = binascii.b2a_base64(image).decode('utf-8')
                        # except Exception as e:
                            # print("Exception binascii.b2a_base64", e)
                            # images.append([url, None])
                        # else:
                        images.append([url, image])
                image_q.put([found_match, images])
        
    # global led
    # global client
    # pcn.print_flash_usage()
    # led_8x8_queue = MsgQueue(20)
    # single_led_queue = MsgQueue(20)
    
    # config['server'] = cfg.broker
    # config["user"] = cfg.user
    # config["password"] = cfg.password
    # config["ssl"] = True
    # config["ssl_params"] = {'server_hostname': cfg.broker}
    # config["queue_len"] = 10  # Use event interface with default queue size
    # config["response_time"] = 30

    # MQTTClient.DEBUG = True  # Optional: print diagnostic messages

    # led_8x8_queue.put([("boot1",False),(cfg.device_letter,False),("boot2",False),(cfg.device_letter,False),])
    # single_led_queue.put("boot")
    # # sw = switch.switch(cfg.switch_pin, client)
    # print("creating asyncio tasks")
    # asyncio.create_task(pcn.led_8x8_display(led_8x8_queue))
    # asyncio.create_task(pcn.do_single_led(single_led_queue))
    # await asyncio.sleep(2)
    # #
    # # make first connection
    # #
    # print("make first connection")
    # client = await pcn.make_first_connection(config, led_8x8_queue, single_led_queue)
    # print("conneted")
    # #
    # asyncio.create_task(raw_messages(client, led_8x8_queue, single_led_queue))
    # asyncio.create_task(pcn.up_so_subscribe(client, led_8x8_queue, single_led_queue, cfg.topics.keys()))
    # asyncio.create_task(pcn.down_report_outage(client, led_8x8_queue, single_led_queue))        
    # led_8x8_queue.put([("all_off", False),("life", False)])
    # single_led_queue.put("all_off")
    # # switch_detected_power = 1 if cfg.switch_type == "NO" else 0  # NO Normaly Open
    # while True:  # Main loop checking to see of other has published
        # print("[publish_check_loop]")
        # await client.publish(cfg.publish, "up")
        # led_8x8_queue.put([("all_off", False),("life", False)])
        # await asyncio.sleep(cfg.number_of_seconds_to_wait)

############ startup ###############
print("run __name__ = %s" %__name__)
if __name__ == "__main__":
    main()
print("exiting, should not get here")
