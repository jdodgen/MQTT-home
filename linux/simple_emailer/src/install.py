# MIT license copyright 2024,25 Jim Dodgen
# this configures and installs software
# it replaces the cfg.py file each time it runs
# Y N defaults are designed for rapid deployment during development
# usage is: "python3 install.py cluster_example.toml"
# this does as much preprocessing as it can to freeup the microprocessor
# see cluster_example.toml
# this reads a toml configuration file see https://toml.io/
# this file is used by install.py to generate device cfg.py files

sensor_to_make = "E simple_emailer"

import os
from pathlib import Path
import datetime
import tomllib
import sys

###### modify these as needed ######
## i use shared source librararys
all_lib_offset="../../../library/" # both linux and micropython
cluster_lib = str(Path.home())+"/Dropbox/wip/pcn_clusters"

# to have  imports from libraries we need to do this:
# Get the absolute path of the current script's directory
# Add the parent directory to sys.path
# In this example, if main.py is in 'project/', this adds 'project/'
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, all_lib_offset))
import feature_power # located in all_lib_offset
# from char8x8 import char8x8 # located in mp_lib_offset
# from esp32s2_flasher import flasher
###### end of stuff that needs modification ######

def load_cluster(cluster_file_name):
    if len(cluster_file_name) > 1:
        cluster_toml = cluster_lib+"/"+cluster_file_name
    else:
        print("testing from current directory")
        cluster_toml = "cluster-example.toml"  # test cluster
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
        only_this_payload = cluster["topic"][topic].get("only_this_payload", "AlL")
        subject = cluster["topic"][topic]["subject"]
        body = cluster["topic"][topic]["body"]
        image_urls = cluster["topic"][topic].get("image_urls", [])
        cc_string = ''
        if "to_list" in cluster["topic"][topic]:
            print("to_list", cluster["topic"][topic]["to_list"])
            for addr in cluster["topic"][topic]["to_list"]:
                cc_string += "<%s>," % (addr,)
            cc_string = cc_string.rstrip(",")
        
        print(topic, mqtt, only_this_payload, subject, body, cc_string,)
        this_email = {"subject": subject, "body": body, "cc_string": cc_string, "image_urls": image_urls, "to_list": cluster["topic"][topic]["to_list"]}
        if mqtt not in l:
            l[mqtt] = {}
        l[mqtt][only_this_payload] = this_email
    #print(l)
    # data structure example for run.py
    for topic in l.keys():
        print("topic", topic)
        for need_payload in l[topic]:
            print("match_on_payload", need_payload)
            if need_payload == True:
                payload = l[topic][need_payload]["only_this_payload"]
                print("needed payload", payload)
            subject = l[topic][need_payload]["subject"]
            print("subject", subject)
    return l

class create_cfg:
    def __init__(self, cluster, sensor_to_make):
        self.cluster = cluster
        self.sensor_to_make = sensor_to_make
        # self.sensors = self.cluster["sensor"]
        self.our_feature = feature_power.feature(self.make_topic(sensor_to_make), publish=True)   # publisher
        print(self.our_feature.topic())
        self.set_cfg_values()
        # self.create_hard_tracked_topics()
        self.pretty_name = "(%s)" % (self.sensor_to_make) #self.sensors[self.sensor_to_make].get("desc", self.sensor_to_make))
        self.topics = load_topics(self.cluster)
        self.write_cfg()
       
    def set_cfg_values(self,):
        pass
        
    def make_topic(self, key):
        print("make_topic", key)
        print("cluster_id",self.cluster["cluster_id"])
        desc = ""
        # sensor = self.sensors.get(key)
        # if sensor:
            # desc = sensor.get("desc", "")
        # else:
            # desc = ""
        if desc == '':
            name =  self.cluster["cluster_id"]+"/"+key
        else:
            name =  self.cluster["cluster_id"]+"/"+key+" "+desc
        return name

    # def general_email_addresses(self):
        # self.cc_string = ''
        # for addr in self.cluster["email"]["to_list"]:
            # self.cc_string += "<%s>," % (addr,)
        # self.cc_string = self.cc_string.rstrip(",")
        # print(self.cc_string)
        
        # self.alert_cc_string = ''
        # if "only_alerts" in self.cluster["email"]:
            # for addr in self.cluster["email"]["only_alerts"]:
                # self.alert_cc_string += "<%s>," % (addr,)
            # self.alert_cc_string = self.alert_cc_string.rstrip(",")
        # print(self.alert_cc_string)
        # return self.cc_string

    # def create_hard_tracked_topics(self):
        # sensor_keys = list(self.sensors.keys())
        # self.hard_tracked_topics = [] # these get tracked from boot. others (soft) only after first publish
        # for key in sensor_keys:
            # if self.sensors[key].get("soft_tracking") == True or self.sensors[key].get("monitor_only") == True:
                    # continue
            # self.hard_tracked_topics.append(feature_power.feature(self.make_topic(key), subscribe=True).topic())
        # print("hard tracked topics", self.hard_tracked_topics)

# this is the cfg.py template uses % to pass in stuff
    def write_cfg(self):
        cfg_template = """
# MIT license copyright 2024, 2025 Jim Dodgen
# this cfg.py was created by: install.py
# Date: %s
# MAKE YOUR CHANGES IN install.py
#
start_delay=0 # startup delay
number_of_seconds_to_wait=30  # all sensors publish "power" messages every 30 seconds
other_message_threshold=4  # how many number_of_seconds_to_wait (2 minutes) to indicate a sensor is down or off
#
broker = '%s'
ssl = %s # true or false
user = '%s'
password = '%s'
#
# gmail account to send emails through
#
gmail_password = "%s" # gmail generates this and it can change it in the future
gmail_user = "%s"
send_messages_to = %s # used for boot email only, see topics for other emails

publish = "%s"
pretty_name = "%s"
cluster_id = "%s"
device_letter = "%s"
topics = %s
"""
        now = datetime.datetime.now()
        cfg_text =  cfg_template % (now.strftime("%Y-%m-%d %H:%M:%S"),
            self.cluster["mqtt_broker"]["broker"],
            self.cluster["mqtt_broker"]["ssl"],
            self.cluster["mqtt_broker"]["user"],
            self.cluster["mqtt_broker"]["password"],
            self.cluster["email"]["gmail_password"],
            self.cluster["email"]["gmail_user"],
            self.cluster["email"]["to_list"],
            self.our_feature.topic(),
            self.pretty_name,
            self.cluster["cluster_id"],
            self.sensor_to_make[0],
            self.topics,
            )
        #print("[%s][%s] [%s]\n%s [%s][%s]\n" % (ssid, wifi_password, broker, to_list,
        #   gmail_password, gmail_user ))
        with open('cfg.py', 'w') as f:
            f.write(cfg_text)
        print("created cfg.py")

def main():
    while True:
        try:
            cluster_name = "cluster_jimdod_simple_emailer.toml"  #sys.argv[1]
        except:
            print("Input cluster toml file name:")
            cluster_name = input()
        try:
            cluster = load_cluster(cluster_name)
            break
        except:
            print("Try again")
            sys.exit()
    #print("request = ", sensor_to_make)
    create_cfg(cluster, sensor_to_make) # drops cfg.py file
    os.system("python3 run.py")

if __name__ == "__main__":
    main()
