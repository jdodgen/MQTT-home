# MIT licence copyright 2026 Jim Dodgen
# subscribe to things, check payloads, and then publish something
version = 1

import time
import multiprocessing
import message
import queue
import database

xprint = print # copy print
my_name = "[triggers_daemon]"
def print(*args, **kwargs): # replace print
    #return  # comment/uncomment to turn print on off
    # do whatever you want to do
    #xprint('statement before print')
    xprint(my_name, *args, **kwargs) # the copied real print
    
def make_trigger_structure(db):
    triggers = {}
    raw_triggers = db.get_all_triggers()
    for t in raw_triggers:
        pub_topic =   t[1]
        pub_payload = t[2].encode()
        sub_topic =   t[3]
        sub_payload = t[4].encode()
        # subscribe to
        if sub_topic not in triggers:
            triggers[sub_topic] = {}
        if sub_payload not in triggers[sub_topic]:
            triggers[sub_topic][sub_payload] = {}
        # publish to
        if pub_topic not in triggers[sub_topic][sub_payload]:
            triggers[sub_topic][sub_payload][pub_topic] = pub_payload
    print(triggers)
    return triggers
        
def task():
    db = database.database()
    q = queue.Queue()  
    msg = message.message(q, my_parent=my_name)
    triggers = make_trigger_structure(db)
    for sub in list(triggers):
        print("sub",sub)
        msg.client.subscribe(sub, 0)
    while True:
        item = q.get(timeout=None)
        print("raw q", item)
        if item[0] == "callback":
            topic = item[1]
            payload = item[2]
            if topic in triggers:
                if payload in triggers[topic]:
                    print("processing", topic, payload)
                    things_to_pub = triggers[topic][payload]
                    for sub_topic, payload in things_to_pub.items():
                        msg.client.publish(sub_topic,payload)
                        print("published:", sub_topic, payload)
                        continue
            print("Error: unknown callback:", topic, payload)

def start_timers_daemon():
    p = multiprocessing.Process(target=task)
    p.start()
    return p
    
if __name__ == "__main__":
    task()
