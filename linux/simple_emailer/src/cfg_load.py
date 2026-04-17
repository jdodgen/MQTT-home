# simple_emailer
# MIT license copyright 2024, 2025 Jim Dodgen
# this cfg.py was created by: install.py
# Date: 2025-12-13 22:17:46
# MAKE YOUR CHANGES IN install.py
#
start_delay=0 # startup delay
number_of_seconds_to_wait=30  # all sensors publish "power" messages every 30 seconds
other_message_threshold=4  # how many number_of_seconds_to_wait (2 minutes) to indicate a sensor is down or off
cluster_file_name = "cluster_simple_emailer.toml"
#
broker = '26d590584baf4655a81048787c932f80.s1.eu.hivemq.cloud'
ssl = True # true or false
user = 'powerchange'
password = 'power!N0w'
#
# gmail account to send emails through
#
gmail_password = "xdom zveb qytq snms" # gmail generates this and it can change it in the future
gmail_user = "notifygenerator@gmail.com"
send_messages_to = ['jim.dodgen@gmail.com'] # used for boot email only, see topics for other emails

publish = "home/jimdod/E1 simple_emailer/power"
#pretty_name = "(E1 simple_emailer)"
cluster_id = "jimdod"
device_letter = "E1"

topics = {'home/jimdod/Front door/quad_chimes': {'AlL': {'subject': 'Front door bell pressed', 'body': 'Three pictures here', 'cc_string': '<jim@dodgen.us>', 'image_urls': [{'url': 'http://192.168.0.4/cgi-bin/snapshot.cgi?channel=1&type=0', 'user': 'admin', 'pw': 'alert.Away'}, {'url': 'http://192.168.0.3/cgi-bin/snapshot.cgi?channel=2&type=0', 'user': 'admin', 'pw': 'dr0wssap!'}, {'url': 'http://192.168.0.3/cgi-bin/snapshot.cgi?channel=4&type=0', 'user': 'admin', 'pw': 'dr0wssap!', 'rotate': -90}], 'to_list': ['jim@dodgen.us'], 'only_on_change_of_payload': False}}, 'home/jimdod/Pub/quad_chimes': {'AlL': {'subject': 'Button on bar pressed', 'body': 'See! it did work!!!', 'cc_string': '<jim@dodgen.us>', 'image_urls': [{'url': 'http://192.168.0.4/cgi-bin/snapshot.cgi?channel=1&type=0', 'user': 'admin', 'pw': 'alert.Away'}], 'to_list': ['jim@dodgen.us'], 'only_on_change_of_payload': False}}, 'home/jimdod/D Garage door/power': {'down': {'subject': 'The Garage door is open', 'body': "by cracky I sence that the carrage house door is open. I hope the horses don't run out.", 'cc_string': '<jim@dodgen.us>', 'image_urls': [{'url': 'http://192.168.0.4/cgi-bin/snapshot.cgi?channel=1&type=0', 'user': 'admin', 'pw': 'alert.Away'}, {'url': 'http://192.168.0.3/cgi-bin/snapshot.cgi?channel=2&type=0', 'user': 'admin', 'pw': 'dr0wssap!'}], 'to_list': ['jim@dodgen.us'], 'only_on_change_of_payload': True}, 'up': {'subject': 'The garage door is closed', 'body': 'Horses be contained, all is well now, ta! ta! cheerio', 'cc_string': '<jim@dodgen.us>', 'image_urls': [{'url': 'http://192.168.0.4/cgi-bin/snapshot.cgi?channel=1&type=0', 'user': 'admin', 'pw': 'alert.Away'}, {'url': 'http://192.168.0.3/cgi-bin/snapshot.cgi?channel=2&type=0', 'user': 'admin', 'pw': 'dr0wssap!'}], 'to_list': ['jim@dodgen.us'], 'only_on_change_of_payload': True}}}

def load_cluster(cluster_toml):
    print("using:", cluster_toml)
    try:
        with open(cluster_toml, 'rb') as toml_file:
            print("cluster_toml opened")
            try:
                cluster = tomllib.load(toml_file)
            except tomllib.TOMLDecodeError as e:
                print(e)
                sys.exit()
            print(cluster)
            return cluster
    except FileNotFoundError:
        print("Error: ",cluster_toml," File not found")
        sys.exit()
    except tomllib.TOMLDecodeError as e:
        print("Error: Invalid TOML format in {file_path}: {e}")
        sys.exit()
    except Exception as e:
        print("cluster_toml open failed", e)

def load_topics(cluster):
    l = {}
    for topic in cluster["topic"]:
        print("\ntopic",topic,"\n")
        mqtt = cluster["topic"][topic]["mqtt_topic"]
        matching_payload = cluster["topic"][topic].get("matching_payload", "AlL")
        only_on_change_of_payload = cluster["topic"][topic].get("only_on_change_of_payload", False)
        subject = cluster["topic"][topic]["subject"]
        body = cluster["topic"][topic]["body"]
        image_urls = cluster["topic"][topic].get("image_urls", [])
        cc_string = ''
        if "to_list" in cluster["topic"][topic]:
            print("to_list", cluster["topic"][topic]["to_list"])
            for addr in cluster["topic"][topic]["to_list"]:
                cc_string += "<%s>," % (addr,)
            cc_string = cc_string.rstrip(",")
        
        print(topic, mqtt, matching_payload, subject, body, cc_string, only_on_change_of_payload)
        this_email = {"subject": subject, "body": body, "cc_string": cc_string, "image_urls": image_urls, "to_list": cluster["topic"][topic]["to_list"], "only_on_change_of_payload": only_on_change_of_payload}
        if mqtt not in l:
            l[mqtt] = {}
        l[mqtt][matching_payload] = this_email
    #print(l)
    # data structure example for run.py
    for topic in l.keys():
        print("topic", topic)
        for need_payload in l[topic]:
            print("match_on_payload", need_payload)
            if need_payload == True:
                payload = l[topic][need_payload]["matching_payload"]
                print("needed payload", payload)
            subject = l[topic][need_payload]["subject"]
            print("subject", subject)
    return l
publish

try:
    cluster = load_cluster(cluster_file_name)
except:
    print(f"could not find  [{cluster_file_name}]")
    sys.exit()
topics = load(cluster)
broker = cluster["mqtt_broker"]["broker"]
ssl = cluster["mqtt_broker"]["ssl"]
user = cluster["mqtt_broker"]["user"]
password = cluster["mqtt_broker"]["password"]
gmail_password = cluster["email"]["gmail_password"]
gmail_user = cluster["email"]["gmail_user"]
send_messages_to = cluster["email"]["to_list"]
default_port = 8883
http_image_timeout = 15
publish = cluster["publish"]
