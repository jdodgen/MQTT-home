# simple_emailer inline confg builder
# MIT license copyright 2024, 2025 Jim Dodgen
# it loads a toml file creating CONSTANTS
# this runs at import and leaves values access like "self.broker = cfg.BROKER"
import tomllib

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
    
# shared items
topics = load_topics(cluster)
print(f"topics {topics}")
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
