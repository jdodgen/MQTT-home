# MIT license copyright 2025 Jim Dodgen
# simple_emailer is built off of Power Change Notifier
# accepts a payload with subject and body and emails to the cfg.py emails
# this version to develop into a framework 
#
# requires only a MQTT Broker. Local or in the Cloud
#
VERSION = (1, 0, 1)
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import ssl
import binascii
import multiprocessing
from mqtt_manager import mqtt_manager
import cfg
import time
import requests
from PIL import Image
import io
from queue import Empty

#client = None
xprint = print # copy print
def print(*args, **kwargs): # replace print
    #return # comment/uncomment to turn print on off
    xprint("[send_emails]", *args, **kwargs) # the copied real print
    
def download_image_data(url_info):
    print("download_image_data", url_info)
    try:
        url = url_info["url"]
        user = url_info.get("user", None)
        pw = url_info.get("pw", None)
        rotate = url_info.get("rotate", 0)
        if user:
            # print("download_image_data doing auth[%s][%s]" % (user, pw))
            response = requests.get(url, auth=requests.auth.HTTPDigestAuth(user, pw))
        else:
            response = requests.get(url)
        if response.status_code == 200:
            image_data = response.content # Read the content as bytes
            response.close()
            #print("image_data len", len(image_data));
            if rotate:
                image_stream = io.BytesIO(image_data)
                img = Image.open(image_stream)
                image_data_rotated = img.rotate(rotate, expand=True)
                output_stream = io.BytesIO()
                image_data_rotated.save(output_stream, format="jpeg")
                return output_stream.getvalue()
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
        
def send_email_task(image_q, cluster_id_only=False):
    print("send_email_task starting")
    chunk_size = 100
    while True:
        found_match, jpgs = image_q.get()
        ident = cfg.cluster_id if cluster_id_only else cfg.pretty_name
        print("send_email_task our id [%s]" % (ident,))
        msg = MIMEMultipart()
        msg['Subject'] = found_match["subject"] # +" "+ident
        msg['From'] = cfg.gmail_user
        msg['To'] = found_match["cc_string"]
        msg['Cc'] = found_match["cc_string"]
        msg.attach(MIMEText(found_match["body"]))
        for url, jpg in jpgs:
            print("send_email_task MIMEImage", url)
            msg_image = MIMEImage(jpg, "jpeg", name="")
            msg.attach(msg_image)
        smtp = smtplib.SMTP('smtp.gmail.com', 587)
        smtp.ehlo()
        smtp.starttls()
        smtp.login(cfg.gmail_user, cfg.gmail_password)
        smtp.send_message(msg)
        smtp.quit()

def main():
    print("main starting")
    mqtt_q = multiprocessing.Queue(10)
    image_q = multiprocessing.Queue(10)
    emailer = multiprocessing.Process(target=send_email_task, args=(image_q,))
    emailer.start()
    
    client = mqtt_manager(mqtt_q)
    toggle_list = {"topic":  "payload",}
    last_publish = 0
    while True:
        #print("waiting for message")
        # topic, payload_raw = mqtt_q.get()
        try:
            topic, payload_raw = mqtt_q.get(block=True, timeout=cfg.number_of_seconds_to_wait)
        except Empty:
            # send PCN alive now
            client.publish_command(cfg.publish,"up")
            last_publish = time.time()
            continue
        now = time.time()
        if last_publish+cfg.number_of_seconds_to_wait < now:
            # send PCN alive now
            client.publish_command(cfg.publish,"up")
            last_publish = now
        payload = payload_raw.decode('utf-8')
        this_topic = cfg.topics.get(topic, None)
        print("main from mqtt_q:message topic[%s], payload[%s] " % (topic, payload))
        if not this_topic:  # just checking 
            print(f"main got a missing subscribe {topic}")
        else:  # good one
            #print("main this_topic:", this_topic)
            print("main keys:",this_topic.keys())
            
            found_match = {}
            if payload in this_topic.keys():  
                found_match = this_topic[payload] # see cfg.py
                if found_match["only_on_change_of_payload"]:
                    print(f"main match on change topic [{topic}][{payload}] toggle list [{toggle_list}]")
                    if topic in toggle_list:
                        print(f"main toggle_list payload [{toggle_list[topic]}] == topic [{topic}]")
                        if toggle_list[topic] == payload: # been here loas time so then bypass
                            print(f"main payload was the same so ignored")
                            continue
                        toggle_list[topic] = payload # update payload
                    else: # new guy
                        toggle_list[topic] = payload
                
                #print("main msg found")
            elif "AlL"  in this_topic.keys():  # this is gets all for mqtt topic ignoring payload
                found_match = this_topic["AlL"]
                #print("main AlL found")
            if found_match:
                print(f"main processing: [{topic}],[{payload}]")
                images = []
                image_urls = found_match["image_urls"]
                for url in image_urls:
                    print("main: processing image")
                    try:
                        image = download_image_data(url)
                    except Exception as e:
                        print("main Exception download_image_data", e)
                        image = None
                    else:
                        #print("got image", url, type(image), image[:50])
                        images.append([url, image])
                image_q.put([found_match, images])
    print("exiting main??")

############ startup ###############
#print("run __name__ = %s" %__name__)
if __name__ == "__main__":
    main()
    print("exiting, should not get here")
