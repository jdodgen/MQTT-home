# simple_emailer inline confg builder
# MIT license copyright 2024, 2025 Jim Dodgen
# it loads a toml file creating CONSTANTS
# this runs at import and leaves values access like "self.broker = cfg.BROKER"
import sys
import tomllib
import sqlite3
import time
import http_common as config

DB_NAME =   config.DB_NAME
OUR_PORT =  config.get_db_config()["broker_mqtt_port"]
  
cluster_path = "cluster_simple_emailer.toml"
my_name = "config"
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
        
def get_config():
    with sqlite3.connect(DB_NAME) as db:
        db.row_factory = sqlite3.Row
        cursor = db.execute("SELECT * FROM config WHERE id = 0")
        row = cursor.fetchone()
        #print("broker: ",row["broker"])
        return row
        
def get_events():
    with sqlite3.connect(DB_NAME) as db:
        db.row_factory = sqlite3.Row
        cursor = db.execute("SELECT * FROM events")
        rows = cursor.fetchall()
        return rows
        
def get_cameras(events_name):
    with sqlite3.connect(DB_NAME) as db:
        db.row_factory = sqlite3.Row
        cursor = db.execute(f'''
            SELECT * FROM cameras 
            JOIN cameras_in_events on cameras_in_events.camera_name =  cameras.camera_name
            WHERE cameras_in_events.events_name = ?
            ''', (events_name,))
        rows = cursor.fetchall()
        print("cam rows: ",rows)
        return rows
  
def get_emails(events_name):
    with sqlite3.connect(DB_NAME) as db:
        db.row_factory = sqlite3.Row
        cursor = db.execute(f'''
            SELECT * FROM emailaddr 
            JOIN emailaddr_in_events on emailaddr_in_events.emailaddr_name =  emailaddr.emailaddr_name
            WHERE emailaddr_in_events.events_name = ?
            ''', (events_name,))
        rows = cursor.fetchall()
        return rows
              
# # simple_emailer
# # MIT license copyright 2024, 2025 Jim Dodgen
# # this cfg.py was created by: install.py
# # Date: 2026-04-22 20:06:59
# # MAKE YOUR CHANGES IN install.py
# #
# start_delay=0 # startup delay
# number_of_seconds_to_wait=30  # all sensors publish "power" messages every 30 seconds
# other_message_threshold=4  # how many number_of_seconds_to_wait (2 minutes) to indicate a sensor is down or off
# #
# broker = '26d590584baf4655a81048787c932f80.s1.eu.hivemq.cloud'
# ssl = True # true or false
# user = 'powerchange'
# password = 'power!N0w'
# default_port = 8883
# http_image_timeout = 15
# #
# # gmail account to send emails through
# #
# gmail_password = "xdom zveb qytq snms" # gmail generates this and it can change it in the future
# gmail_user = "notifygenerator@gmail.com"
# send_messages_to = ['jim.dodgen@gmail.com'] # used for boot email only, see topics for other emails

# publish = "home/jimdod/EMAILER simple_emailer/power"
# pretty_name = "(EMAILER simple_emailer)"
# cluster_id = "jimdod"
# device_letter = "EMAILER"
topics = {'home/jimdod/Front door/quad_chimes': 
            {'AlL': 
                 {'subject': 'Front door bell pressed', 'body': 'Three pictures here', 
                 'cc_string': '<jim@dodgen.us>,<jan@dodgen.us>', 
                 'image_urls': [{'url': 'http://192.168.0.4/cgi-bin/snapshot.cgi?channel=1&type=0', 
                 'user': 'admin', 'pw': 'alert.Away'}, 
                                 {'url': 'http://192.168.0.3/cgi-bin/snapshot.cgi?channel=2&type=0', 
                                 'user': 'admin', 'pw': 'dr0wssap!'}, {'url': 'http://192.168.0.3/cgi-bin/snapshot.cgi?channel=4&type=0', 'user': 'admin', 'pw': 'dr0wssap!', 'rotate': -90}], 'to_list': ['jim@dodgen.us', 'jan@dodgen.us'], 'only_on_change_of_payload': False}}, 'home/jimdod/Pub/quad_chimes': {'AlL': {'subject': 'Button on bar pressed', 'body': 'See! it did work!!!', 'cc_string': '<jim@dodgen.us>', 'image_urls': [{'url': 'http://192.168.0.4/cgi-bin/snapshot.cgi?channel=1&type=0', 'user': 'admin', 'pw': 'alert.Away'}], 'to_list': ['jim@dodgen.us'], 'only_on_change_of_payload': False}}, 'home/jimdod/GAR Garage door/power': {'down': {'subject': 'The Garage door is open', 'body': "by cracky I sence that the carrage house door is open. I hope the horses don't run out.", 'cc_string': '<jan@dodgen.us>,<jim@dodgen.us>', 'image_urls': [{'url': 'http://192.168.0.4/cgi-bin/snapshot.cgi?channel=1&type=0', 'user': 'admin', 'pw': 'alert.Away'}, {'url': 'http://192.168.0.3/cgi-bin/snapshot.cgi?channel=2&type=0', 'user': 'admin', 'pw': 'dr0wssap!'}], 'to_list': ['jan@dodgen.us', 'jim@dodgen.us'], 'only_on_change_of_payload': True}, 'up': {'subject': 'The garage door is closed', 'body': 'Horses be contained, all is well now, ta! ta! cheerio', 'cc_string': '<jim@dodgen.us>,<jan@dodgen.us>', 'image_urls': [{'url': 'http://192.168.0.4/cgi-bin/snapshot.cgi?channel=1&type=0', 'user': 'admin', 'pw': 'alert.Away'}, {'url': 'http://192.168.0.3/cgi-bin/snapshot.cgi?channel=2&type=0', 'user': 'admin', 'pw': 'dr0wssap!'}], 'to_list': ['jim@dodgen.us', 'jan@dodgen.us'], 'only_on_change_of_payload': True}}}


def load_db_topics():
    l = {}
    event = get_events()
    for t in event:
        mqtt_topic = t["mqtt_topic"]
        print("\ntopic",mqtt_topic,"\n")
        
        #mqtt_topic = cluster["topic"][topic]["mqtt_topic"]
        if t["matching_payload"]:
            matching_payload=  t["matching_payload"]
        else:
            matching_payload= "AlL"
        only_on_change_of_payload = t["only_on_change_of_payload"]
        subject =   t["subject"]
        body =      t["body"]
        image_urls = get_cameras(t["events_name"])
        bunch_of_images = []
        for i in image_urls:
            bunch_of_images.append({"url": i["url"], 'user': i['user'], 'pw': i["password"], 'rotate': i["rotate"]})
        l["image_urls"] = bunch_of_images
        emails = get_emails(t["events_name"])
        email_string = ""
        for e in emails:
            email_string += f"<{e['email_address']}>,"
        if not email_string:
            print("missing emails? ignoring")
            continue
        l["cc_string"] = email_string[:-1]
        # image_urls = cluster["topic"][topic].get("image_urls", [])
        # cc_string = ''
        # if "to_list" in cluster["topic"][topic]:
            # print("to_list", cluster["topic"][topic]["to_list"])
            # for addr in cluster["topic"][topic]["to_list"]:
                # cc_string += "<%s>," % (addr,)
            # cc_string = cc_string.rstrip(",")
        
        print(mqtt_topic, matching_payload, subject, body, email_string, only_on_change_of_payload)
        this_email = {"subject": subject, "body": body, "cc_string": email_string, 
            "image_urls": image_urls, "to_list": email_string, 
            "only_on_change_of_payload": only_on_change_of_payload}
        
        if mqtt_topic not in l:
            l[mqtt_topic] = {}
        l[mqtt_topic][matching_payload] = this_email
    #print(l)
    # data structure example for run.py
    # for topic in l.keys():
        # print("topic", topic)
        # for need_payload in l[topic]:
            # print("match_on_payload", need_payload)
            # if need_payload == True:
                # payload = l[topic][need_payload]["matching_payload"]
                # print("needed payload", payload)
            # subject = l[topic][need_payload]["subject"]
            # print("subject", subject)
    return {mqtt_topic: 
            {matching_payload: l}}
    #return l

try:
    config = get_config()
except Exception as e:
    print(f"could not get config",e)
    time.sleep(10)
    sys.exit()
    
# things for send_emails built at boot, now static
TOPICS = load_db_topics()
BROKER = config["broker"]
SSL = config["ssl"]
USER = config["user"]
PASSWORD = config["password"]
GMAIL_PASSWORD = config["gmail_password"]
GMAIL_USER = config["gmail_user"]
PCN_TOPIC = config["publish"]

print(f"BROKER [{BROKER}] SSL [{SSL}] USER [{USER}] PASSWORD [{PASSWORD}]\n\tGMAIL_PASSWORD [{GMAIL_PASSWORD}] GMAIL_USER  [{GMAIL_PASSWORD}] ALIVE_PUBLISH  [{ALIVE_PUBLISH}] ")
print("TOPICS->", TOPICS)

DEFAULT_PORT = 8883
ALIVE_INTERVAL = 30
HTTP_IMAGE_TIMEOUT = 15
