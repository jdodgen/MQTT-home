# MIT licence copyright 2026 Jim Dodgen
# subscribe to things, check payloads, and then publish something
version = 1

import time
import multiprocessing
import message
import queue
import database

my_name = "triggers_daemon"
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

def make_trigger_structure(db):
    triggers = {}
    raw_triggers = db.get_all_triggers()
    #import pprint
    #pprint.pprint(f"\ncurrent_triggers:{[dict(row) for row in raw_triggers]}\n")
    for t in raw_triggers:
        #print(F"t[1] = {t[1]} T['ptopic'] {t['ptopic']}")
        pub_topic =   t["ptopic"]
        pub_payload = t["pub_payload"].encode()
        sub_topic =   t["stopic"]
        sub_payload = t["sub_payload"].encode()
        # subscribe to
        if sub_topic not in triggers:
            triggers[sub_topic] = {}
        if sub_payload not in triggers[sub_topic]:
            triggers[sub_topic][sub_payload] = []
        triggers[sub_topic][sub_payload].append([pub_topic, pub_payload])
    print(f"trigger_structure: {triggers}")
    return triggers

def task():
    db = database.database(row_factory=True)
    q = queue.Queue()  
    triggers = make_trigger_structure(db)
    msg = message.message(q, my_parent=my_name)
    for sub in list(triggers):
        print("sub",sub)
        msg.client.subscribe(sub, 0)
    while True:
        item = q.get(timeout=None)
        print("raw q", item)
        if item[0] == "callback":
            topic = item[1]
            payload = item[2]
            process_request(topic, payload)

def process_request():
    if topic in triggers: # subscribed payload
        if payload in triggers[topic]: # payload we want, ignore others
            print("processing", topic, payload)
            things_to_pub = triggers[topic][payload]
            for pub_topic, pub_payload in things_to_pub.items():
                print(f"publishing: {pub_topic}...{pub_payload}")
                msg.client.publish(pub_topic,pub_payload)
    else:
        print(f"Error: unknown topic?:{topic}...{payload}")

if __name__ == "__main__":
    task()
