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

#client = None
xprint = print # copy print
def print(*args, **kwargs): # replace print
    #return # comment/uncomment to turn print on off
    xprint("[run]", *args, **kwargs) # the copied real print
    
def download_image_data(url_info):
    print("download_image_data", url_info)
    try:
        url = url_info["url"]
        user = url_info.get("user", None)
        pw = url_info.get("pw", None)
        rotate = url_info.get("rotate", 0)
        if user:
            print("download_image_data doing auth[%s][%s]" % (user, pw))
            response = requests.get(url, auth=requests.auth.HTTPDigestAuth(user, pw))
        else:
            response = requests.get(url)
        if response.status_code == 200:
            image_data = response.content # Read the content as bytes
            response.close()
            print("image_data len", len(image_data));
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
        idd = cfg.cluster_id if cluster_id_only else cfg.pretty_name
        print("our id [%s]" % (id,))
        msg = MIMEMultipart()
        msg['Subject'] = found_match["subject"] # +" "+idd
        msg['From'] = cfg.gmail_user
        msg['To'] = found_match["cc_string"]
        msg['Cc'] = found_match["cc_string"]
        msg.attach(MIMEText(found_match["body"]))
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

def main():
    mqtt_q = multiprocessing.Queue(10)
    image_q = multiprocessing.Queue(10)
    emailer = multiprocessing.Process(target=send_email_task, args=(image_q,))
    emailer.start()
    client = mqtt_manager(mqtt_q)
    toggle_list = {"topic":  "payload",}
    while True:
        print("waiting for message")
        topic, payload_raw = mqtt_q.get()
        payload = payload_raw.decode('utf-8')
        this_topic = cfg.topics.get(topic, None)
        print("from mqtt_q: topic[%s], payload[%s] " % (topic, payload))
        if this_topic:  # just checking
           
            #print("main this_topic:", this_topic)
            #print("keys:",this_topic.keys())
            
            found_match = {}
            if payload in this_topic.keys():  
                found_match = this_topic[payload]
                if found_match["only_on_change_of_payload"]:
                    if topic in toggle_list and toggle_list[topic] == payload: # then bypass
                        continue
                    else: # different or new payload
                        toggle_list[topic] = payload
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
                        #print("got image", url, type(image), image[:50])
                        images.append([url, image])
                image_q.put([found_match, images])

############ startup ###############
print("run __name__ = %s" %__name__)
if __name__ == "__main__":
    main()
print("exiting, should not get here")
