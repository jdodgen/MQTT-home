# MIT license copyright 2025,2026 Jim Dodgen
# simple_emailer 
# emails a pre-defined collection of ip camera jpgs as well as some text.
# to a one or more email addresses 
# triggered by a MQTT topic and payload (optional)
# requires only a MQTT Broker.
# all contained in a config.py file
# can run on command line/systemd or 
# included in other projects using start_daemon()
#
VERSION = (2, 0, 0)
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import ssl
import binascii
import multiprocessing
from mqtt_manager import mqtt_manager
import config
import time
import requests
from PIL import Image
import io
from queue import Empty

#client = None
my_name = "send_emails"
xprint = print # copy print
def print(*args, **kwargs): # replace print
    #return # comment/uncomment to turn print on off
    try:
        if isinstance(args, tuple) :
            area, comment = args[0].split(None,1)
            comment += " "+" ".join(list(args[1:]))
        else:
            area, comment = args[0].split(None,1)    
        xprint("["+my_name+"/"+area+"]",comment, **kwargs)
    except:
        xprint(f"[{my_name}]", *args, **kwargs) # the copied real print
    
def download_image_data(url_info):
    print(f"download_image_data [{url_info['url']}][{url_info.get('user', '')},{url_info.get('pw', '')}]")
    try:
        url = url_info["url"]
        user = url_info.get("user", None)
        pw = url_info.get("pw", None)
        rotate = url_info.get("rotate", 0)
        if user:
            # print("download_image_data doing auth[%s][%s]" % (user, pw))
            try:
                print("download_image_data doing auth[%s][%s]" % (user, pw))
                response = requests.get(url, auth=requests.auth.HTTPDigestAuth(user, pw), timeout=config.HTTP_IMAGE_TIMEOUT)
                print("download_image_data requests.get returned")
            except requests.exceptions.RequestException as e:
                print(f"download_image_data requests.get  with user Error: [{e}]")
                return None
        else:
            try:
                response = requests.get(url)
            except Exception as e:
                print(f"download_image_data requests.get  NO user Error: [{e}]")
                return None
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
                #print("download_image_data returning rotate") 
                return output_stream.getvalue()
            #print("download_image_data returning normal")
            return image_data
        else:
            print(f"download_image_data Failed to download image. Status code:[{response.status_code}]")
            image_data = None
            response.close() 
            return None
    except Exception as e:
        image_data = None
        print(f"download_image_data Error during HTTP request: [{e}]")
        return None       
        
def send_email_task(emailer_q): #, cluster_id_only=False):
    print("send_email_task starting")
    chunk_size = 100
    while True:
        found_match, jpgs = emailer_q.get()
        # print("send_email_task our id [%s]" % (ident,))
        msg = MIMEMultipart()
        msg['Subject'] = found_match["subject"] # +" "+ident
        msg['From'] = config.GMAIL_USER
        msg['To'] = found_match["cc_string"]
        msg['Cc'] = found_match["cc_string"]
        msg.attach(MIMEText(found_match["body"]))
        for url, jpg in jpgs:
            print(f"send_email_task MIMEImage[{url['url']}]")
            msg_image = MIMEImage(jpg, "jpeg", name="")
            msg.attach(msg_image)
        try:
            print("send_email_task  SMTP")
            smtp = smtplib.SMTP('smtp.gmail.com', 587)
            smtp.ehlo()
            smtp.starttls()
            smtp.login(config.GMAIL_USER, config.GMAIL_PASSWORD)
            smtp.send_message(msg)
            smtp.quit()
        except:
            print("send_email_task  FAILED")
            time.sleep(1)

def main():
    print("main starting")
    mqtt_q = multiprocessing.Queue(10)
    emailer_q = multiprocessing.Queue(10)
    emailer = multiprocessing.Process(target=send_email_task, args=(emailer_q,))
    emailer.start()
    
    client = mqtt_manager(mqtt_q)
    toggle_list = {"topic":  "payload",}
    last_publish = 0
    while True:
        #print("waiting for message")
        # topic, payload_raw = mqtt_q.get()
        #
        # MAIN LOOP
        #
        try:
            topic, payload_raw = mqtt_q.get(block=True, timeout=config.ALIVE_INTERVAL)
        except Empty:
            # send PCN alive now
            try:
                client.publish_command(config.ALIVE_PUBLISH,"up")
                last_publish = time.time()
            except Exception as e:
                print(f"main publish up failed {e}")
            if not emailer.is_alive():
                print("main emailer process dead")
            continue
        now = time.time()
        if last_publish+config.ALIVE_INTERVAL < now:
            # send PCN alive now
            client.publish_command(config.ALIVE_PUBLISH,"up")
            last_publish = now
        payload = payload_raw.decode('utf-8')
        this_topic = config.TOPICS.get(topic, None)
        print("main from mqtt_q:message topic[%s], payload[%s] " % (topic, payload))
        if not this_topic:  # just checking 
            print(f"main got a missing subscribe {topic}")
        else:  # good one
            #print("main this_topic:", this_topic)
            print("main this_topic.keys:",this_topic.keys())
            found_match = {}
            
            if payload in this_topic.keys():  
                found_match = this_topic[payload] # see config.py for the data structure
                if found_match["only_on_change_of_payload"]:
                    #print(f"main match on change topic [{topic}][{payload}] toggle list [{toggle_list}]")
                    if topic in toggle_list:
                        print(f"main toggle_list[{toggle_list[topic]}] ==  payload [{payload}]")
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
                print(f"main found_match: [{topic}],[{payload}]")
                images = []
                image_urls = found_match["image_urls"]
                # url's loop
                for url in image_urls:
                    print("main getting download_image_data")
                    try:
                        image = download_image_data(url)
                        if image is None:
                            print("main download_image_data returned None")
                    except Exception as e:
                        print(f"main Exception download_image_data: [{e}]")
                        image = None
                    else:
                        #print("got image", url, type(image), image[:50])
                        print("main got image")
                        if image:
                            images.append([url, image])
                print("main emailer_q.put emailer")
                emailer_q.put([found_match, images])
    print("exiting main??")
    
def start_daemon():
    p = multiprocessing.Process(target=main)
    p.start()
    return p
    
############ CLI startup ###############
if __name__ == "__main__":
    main()
    print("exiting, should not get here")
