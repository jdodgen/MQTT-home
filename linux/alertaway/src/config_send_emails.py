# simple_emailer inline confg builder
# MIT license copyright 2024, 2025, 2026 Jim Dodgen
# it loads a toml file creating CONSTANTS
# this runs at import and leaves STATIC values
# access like "self.broker = cfg.BROKER"
import sys
import signal
import tomllib
#import sqlite3
import time
from  pprint import pprint
import http_common as config
  
#cluster_path = "cluster_simple_emailer.toml"
my_name = "config_send_emails"
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
        
# def get_config():
    # with config.db_connect_sync() as db:
        # cursor = db.execute("SELECT * FROM config WHERE id = 0")
        # row = cursor.fetchone()
        # #print("broker: ",row["broker"])
        # return dict(row)
        
def get_events():
    with config.db_connect_sync() as db:
        cursor = db.execute("SELECT * FROM events")
        rows = cursor.fetchall()
        return rows
        
def get_cameras(events_name):
    with config.db_connect_sync() as db:
        cursor = db.execute(f'''
            SELECT * FROM cameras 
            JOIN cameras_in_events on cameras_in_events.camera_name =  cameras.camera_name
            WHERE cameras_in_events.events_name = ?
            ''', (events_name,))
        rows = cursor.fetchall()
        return rows
  
def get_emails(events_name):
    with config.db_connect_sync() as db:
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
example_topics = {'home/jimdod/Front door/quad_chimes': 
                            {None: 
                                     {  'subject': 'Front door bell pressed', 'body': 'Three pictures here', 
                                        'cc_string': '<jim@dodgen.us>,<jan@dodgen.us>', 
                                        'image_urls': [ {
                                                        'url': 'http://192.168.0.4/cgi-bin/snapshot.cgi?channel=1&type=0', 
                                                        'user': 'admin', 
                                                        'pw': 'alertdtaway'
                                                        }, 
                                                        {
                                                        'url': 'http://192.168.0.3/cgi-bin/snapshot.cgi?channel=2&type=0', 
                                                        'user': 'admin', 
                                                        'pw': 'passwd'
                                                        }, 
                                                        {
                                                        'url': 'http://192.168.0.3/cgi-bin/snapshot.cgi?channel=4&type=0', 
                                                        'user': 'admin', 
                                                        'pw': 'dr0wssap!', 
                                                        'rotate': -90
                                                        }
                                                      ], 
                                            'to_list': ['jim@dodgen.us', 'jan@dodgen.us'], 
                                            'only_on_change_of_payload': False
                                   }
                          }, 
               'home/jimdod/Pub/quad_chimes': {None: {'subject': 'Button on bar pressed', 'body': 'See! it did work!!!', 'cc_string': '<jim@dodgen.us>', 'image_urls': [{'url': 'http://192.168.0.4/cgi-bin/snapshot.cgi?channel=1&type=0', 'user': 'admin', 'pw': 'alert.Away'}], 'to_list': ['jim@dodgen.us'], 'only_on_change_of_payload': False}}, 'home/jimdod/GAR Garage door/power': {'down': {'subject': 'The Garage door is open', 'body': "by cracky I sence that the carrage house door is open. I hope the horses don't run out.", 'cc_string': '<jan@dodgen.us>,<jim@dodgen.us>', 'image_urls': [{'url': 'http://192.168.0.4/cgi-bin/snapshot.cgi?channel=1&type=0', 'user': 'admin', 'pw': 'alert.Away'}, {'url': 'http://192.168.0.3/cgi-bin/snapshot.cgi?channel=2&type=0', 'user': 'admin', 'pw': 'dr0wssap!'}], 'to_list': ['jan@dodgen.us', 'jim@dodgen.us'], 'only_on_change_of_payload': True}, 'up': {'subject': 'The garage door is closed', 'body': 'Horses be contained, all is well now, ta! ta! cheerio', 'cc_string': '<jim@dodgen.us>,<jan@dodgen.us>', 'image_urls': [{'url': 'http://192.168.0.4/cgi-bin/snapshot.cgi?channel=1&type=0', 'user': 'admin', 'pw': 'alert.Away'}, {'url': 'http://192.168.0.3/cgi-bin/snapshot.cgi?channel=2&type=0', 'user': 'admin', 'pw': 'dr0wssap!'}], 'to_list': ['jim@dodgen.us', 'jan@dodgen.us'], 'only_on_change_of_payload': True}}}

def build_a_payload(event):
        if event["matching_payload"]:
            matching_payload=  event["matching_payload"]
        else:
            matching_payload= None
        list_of_images = []
        image_urls = get_cameras(event["events_name"])
        for i in image_urls:
            print(f'/n]ngetting image [{i["camera_name"]}]')
            d = {"url": i["url"], 'user': i['user'], 'pw': i["password"], 'rotate': i["rotate"]}
            #print("url",d)
            #print("\n\n")
            list_of_images.append(d)
        
        #print(f"\nmatching_payload[{matching_payload}]\n")
        only_on_change_of_payload = event["only_on_change_of_payload"]
        subject =   event["subject"]
        body =      event["body"]
        emails = get_emails(event["events_name"])
        email_string = ""
        for e in emails:
            email_string += f"<{e['email_address']}>,"
        if not email_string:
            print("missing emails? ignoring")
            return None
        complete_event = {"subject": subject, "body": body, "cc_string": email_string[:-1], 
            "image_urls": list_of_images, "to_list": email_string[:-1], 
            "only_on_change_of_payload": only_on_change_of_payload}
        #pprint(complete_event)
        return complete_event
    

def load_db_topics():
    all_topics = {}
    events = get_events()
    if not events:
        return None 
    for t in events:
        mqtt_topic = t["mqtt_topic"]
        payload_event = build_a_payload(t)
        if mqtt_topic not in all_topics:
            all_topics[mqtt_topic] = {}
        all_topics[mqtt_topic][t["matching_payload"]] = payload_event
        #print("\ntopic",mqtt_topic,"\n")
        
        #mqtt_topic = cluster["topic"][topic]["mqtt_topic"]
        # if t["matching_payload"]:
            # matching_payload=  t["matching_payload"]
        # else:
            # matching_payload= None
        # print(f"\n\nload_db_topics topic[{mqtt_topic}]\nmatching_payload[{matching_payload}]\n\n")
        # only_on_change_of_payload = t["only_on_change_of_payload"]
        # subject =   t["subject"]
        # body =      t["body"]
        # image_urls = get_cameras(t["events_name"])
        # list_of_images = []
        # for i in image_urls:
            # print(f"getting image [{camera_name}]")
            # url = {"url": i["url"], 'user': i['user'], 'pw': i["password"], 'rotate': i["rotate"]}
            # list_of_images.append(url)
        # all_topics["image_urls"] = list_of_images
        # emails = get_emails(t["events_name"])
        # email_string = ""
        # for e in emails:
            # email_string += f"<{e['email_address']}>,"
        # if not email_string:
            # print("missing emails? ignoring")
            # continue
        # all_topics["cc_string"] = email_string[:-1]
        # # image_urls = cluster["topic"][topic].get("image_urls", [])
        # # cc_string = ''
        # # if "to_list" in cluster["topic"][topic]:
            # # print("to_list", cluster["topic"][topic]["to_list"])
            # # for addr in cluster["topic"][topic]["to_list"]:
                # # cc_string += "<%s>," % (addr,)
            # # cc_string = cc_string.rstrip(",")
        
        # print(mqtt_topic, matching_payload, subject, body, email_string, only_on_change_of_payload)
        # this_email = {"subject": subject, "body": body, "cc_string": email_string, 
            # "image_urls": image_urls, "to_list": email_string, 
            # "only_on_change_of_payload": only_on_change_of_payload}
        
        # if mqtt_topic not in all_topics:
            # all_topics[mqtt_topic] = {}
        # all_topics[mqtt_topic][matching_payload] = this_email
    #print(all_topics)
    # data structure example for run.py
    # for topic in all_topics.keys():
        # print("topic", topic)
        # for need_payload in all_topics[topic]:
            # print("match_on_payload", need_payload)
            # if need_payload == True:
                # payload = all_topics[topic][need_payload]["matching_payload"]
                # print("needed payload", payload)
            # subject = all_topics[topic][need_payload]["subject"]
            # print("subject", subject)
    
        #print(f"\n\nload_db_topics topic[{mqtt_topic}]\nmatching_payload[{matching_payload}]\n\n")
    
    # xprint("all_topics", all_topics)
    # return {mqtt_topic: 
            # {matching_payload: all_topics}}
    #return all_topics
    print("\n\n")
    pprint(all_topics)
    return all_topics 

try:
    db_config = config.get_db_config()
except Exception as e:
    print(f"could not get db_config",e)
    time.sleep(10)
    sys.exit()
    
# things for send_emails built at boot, now static
TOPICS = load_db_topics()
if not TOPICS:
    print("Nothing to do, sleeping")
    signal.pause()  # nothing to do so sleep forever waiting on a systemd restart and something to do 
BROKER = db_config["local_broker_ip"]
OUR_PORT =  db_config["local_broker_port"]
SSL = db_config["local_broker_ssl"]
USER = db_config["local_broker_user"]
PASSWORD = db_config["local_broker_password"]
GMAIL_PASSWORD = db_config["gmail_password"]
GMAIL_USER = db_config["gmail_user"]
PCN_TOPIC = db_config["publish"]

# print(f"BROKER [{BROKER}] SSL [{SSL}] USER [{USER}] PASSWORD [{PASSWORD}]\n\tGMAIL_PASSWORD [{GMAIL_PASSWORD}] GMAIL_USER  [{GMAIL_PASSWORD}]")
# print("TOPICS >>>>>>>>>>>> ", TOPICS)

DEFAULT_PORT = 8883
ALIVE_INTERVAL = 30
