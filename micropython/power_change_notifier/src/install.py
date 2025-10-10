# MIT license copyright 2024,25 Jim Dodgen
# this configures and installs software
# it replaces the cfg.py file each time it runs
# Y N defaults are designed for rapid deployment during development
# usage is: "python3 install.py cluster_example.toml"
# this does as much preprocessing as it can to freeup the microprocessor
# see cluster_example.toml
# this reads a toml configuration file see https://toml.io/
# this file is used by install.py to generate device cfg.py files

import os
from pathlib import Path
import datetime
import tomllib
import sys

###### modify these as needed ######
## i use shared source librararys
mp_lib_offset="../../library/"  # micropython specific
all_lib_offset="../../../library/" # both linux and micropython
cluster_lib = str(Path.home())+"/Dropbox/wip/pcn_clusters"


if os.name == 'nt':
    serial_port = "COM3"
else: # linux
    serial_port = "/dev/ttyACM0"
print("Device on:", serial_port)

# to have  imports from libraries we need to do this:
# Get the absolute path of the current script's directory
# Add the parent directory to sys.path
# In this example, if main.py is in 'project/', this adds 'project/'
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, all_lib_offset))
sys.path.append(os.path.join(current_dir, mp_lib_offset))
import feature_power # located in all_lib_offset
from char8x8 import char8x8 # located in mp_lib_offset
from esp32s2_flasher import flasher
###### end of stuff that needs modification ######

def load_cluster(cluster_file_name):
    if len(cluster_file_name) > 1:
        cluster_toml = cluster_lib+"/"+cluster_file_name
    else:
        print("testing from current directory")
        cluster_toml = "cluster-example.toml"  # test cluster
    try:
        with open(cluster_toml, 'rb') as toml_file:
            cluster = tomllib.load(toml_file)
            print(cluster)
            return cluster
               
    except FileNotFoundError:
        print("Error: ",cluster_toml," File not found")
        sys.exit()
    except tomllib.TOMLDecodeError as e:
        print("Error: Invalid TOML format in {file_path}: {e}")
        sys.exit()
        
def wifi_list_of_list(cluster):
    l = []
    for ssid in cluster["network"]:
        print("ssid", ssid)
        pw = cluster["network"][ssid]["password"]
        print("password", cluster["network"][ssid]["password"])
        l.append([ssid, pw])
    print(l)
    return l
        
def print_sensors(sensors):
    sensor_keys = list(sensors.keys())
    sensor_keys.sort()
    for key in sensor_keys:
        #print("sensor key=", key)
        if len(key) != 1:
            print("id [%s] mist be a single letter or number" % (key, ))
        try:
            desc =sensors[key]["desc"]
        except:
            desc=""
        print("%s) %s" % (key, desc))
        if(('+' in desc) or ('/' in desc) or ('+' in key) or ('/' in key)):
            print("\nERROR: future topic  [%s][%s] contains a / or +,  MQTT reserved fix in toml file\n" % (key,desc,))
            sys.exit()

class create_cfg:
    def __init__(self, cluster, sensor_to_make):
        self.cluster = cluster
        self.sensor_to_make = sensor_to_make
        self.sensors = self.cluster["sensor"]
        self.our_feature = feature_power.feature(self.make_topic(sensor_to_make), publish=True)   # publisher
        print(self.our_feature.topic())
        self.set_cfg_values()
        self.create_hard_tracked_topics()
        self.c8x8 = char8x8(invert=self.cluster.get("invert_8x8", False))
        self.pretty_name = "From: %s %s" % (self.sensor_to_make, self.sensors[self.sensor_to_make].get("desc", self.sensor_to_make))
        self.write_cfg()
       
    def set_cfg_values(self,):
        self.wifi=wifi_list_of_list(self.cluster);
        if self.sensor_to_make in self.sensors:
            desc = self.sensors[self.sensor_to_make].get("desc")

            #self.publish_to = self.sensor_to_make+" "+desc if desc else self.sensor_to_make

            self.send_email = self.sensors[self.sensor_to_make].get("send_email",False)
            
            #self.ssid = self.sensors[self.sensor_to_make].get("ssid", self.cluster["network"]["ssid"])
            #self.wifi_password = self.sensors[self.sensor_to_make].get("wifi_password", self.cluster["network"]["wifi_password"])
            
            self.monitor_only = self.sensors[self.sensor_to_make].get("monitor_only", False)
            self.switch = self.sensors[self.sensor_to_make].get("switch", False)
            self.switch_type = self.sensors[self.sensor_to_make].get("switch_type","NO")

        else:  # these "letters" do not exist in the toml file but are treated as "soft_tracking"  that is not tracked until first publish
            #self.publish_to = self.sensor_to_make   # single letter version
            self.send_email = False
            
            #self.ssid = self.cluster["network"]["ssid"]
            #self.wifi_password = self.cluster["network"]["wifi_password"]
            
            self.monitor_only = False
            self.switch = False
            self.switch_type = False
        print("send_email [%s] wifi[%s] monitor_only [%s] switch [%s] switch_type [%s]" %
            (self.send_email, self.wifi, self.monitor_only, self.switch, self.switch_type))
        self.email_addresses()

    def make_topic(self, key):
        print("make_topic", key)
        print("cluster_id",self.cluster["cluster_id"])
        sensor = self.sensors.get(key)
        if sensor:
            desc = sensor.get("desc", "")
        else:
            desc = ""
        if desc == '':
            name =  self.cluster["cluster_id"]+"/"+key
        else:
            name =  self.cluster["cluster_id"]+"/"+key+" "+desc
        return name

    def email_addresses(self):
        self.cc_string = ''
        for addr in self.cluster["email"]["to_list"]:
            self.cc_string += "<%s>," % (addr,)
        self.cc_string = self.cc_string.rstrip(",")
        print(self.cc_string)
        return self.cc_string

    def create_hard_tracked_topics(self):
        sensor_keys = list(self.sensors.keys())
        self.hard_tracked_topics = [] # these get tracked from boot. others (soft) only after first publish
        for key in sensor_keys:
            if self.sensors[key].get("soft_tracking") == True or self.sensors[key].get("monitor_only") == True:
                    continue
            self.hard_tracked_topics.append(feature_power.feature(self.make_topic(key), subscribe=True).topic())
        print("hard tracked topics", self.hard_tracked_topics)

# this is the cfg.py template uses % to pass in stuff
    def write_cfg(self):
        cfg_template = """
# MIT license copyright 2024, 2025 Jim Dodgen
# this cfg.py was created by: install.py
# Date: %s
# MAKE YOUR CHANGES IN install.py
#
# current pin assignements
big_led_pin        = 3  # D3" on D1-Mini proto card
onboard_led_pin   = 15  # built-in BLUE led
switch_pin        = 12  # D8 # shared with button_pin
button_pin        = 12  # D8
play_all_pin      = 35  # D1
ding_dong_pin     = 33  # D2
ding_ding_pin     = 18  # D3
westminster_pin   = 16  # D4
data8x8_pin       = 11  # D7
clock8X8_pin      = 7   # D5

brightness8x8 = 0  # half
#
#wifi: IoT or guest network recommended
wifi= %s
#
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
# a python list of one or more email addresses ["9095551212@tmomail.net", "you@gmail.com"]
send_messages_to = %s # a python list
#
# gmail account to send emails through
#
gmail_password = "%s" # gmail generates this and it can change it in the future
gmail_user = "%s"
cc_string = "%s"  # a smtp Cc: string

publish = "%s"
pretty_name = "%s"
cluster_id = "%s"
send_email =  %s
hard_tracked_topics = %s # these get tracked from boot, others only after first publish
monitor_only = %s  # if True this sensor does not publish status and therefore is not tracked
switch = %s # if true then "switch_gpio" is tested if off then no publish will be sent
switch_type = "%s" # for "NO or NC defaults to "NO". So when "closed" no "power" publishes are sent
tm1640_chars = %s
device_letter = "%s"

"""
        now = datetime.datetime.now()
        cfg_text =  cfg_template % (now.strftime("%Y-%m-%d %H:%M:%S"),
            self.wifi,
            self.cluster["mqtt_broker"]["broker"],
            self.cluster["mqtt_broker"]["ssl"],
            self.cluster["mqtt_broker"]["user"],
            self.cluster["mqtt_broker"]["password"],
            self.cluster["email"]["to_list"],
            self.cluster["email"]["gmail_password"],
            self.cluster["email"]["gmail_user"],
            self.cc_string,
            self.our_feature.topic(),
            self.pretty_name,
            self.cluster["cluster_id"],
            self.send_email,
            self.hard_tracked_topics,
            self.monitor_only,
            self.switch,
            self.switch_type,
            self.c8x8.create_tm1640_dict(),
            self.sensor_to_make[0],
            )
        #print("[%s][%s] [%s]\n%s [%s][%s]\n" % (ssid, wifi_password, broker, to_list,
        #   gmail_password, gmail_user ))
        with open('cfg.py', 'w') as f:
            f.write(cfg_text)
        print("created cfg.py")

def push_library_code():
    code = [
    mp_lib_offset+"main.py",
    mp_lib_offset+"boot.py",
    mp_lib_offset+"uuid.py",
    mp_lib_offset+"alert_handler.py",
    mp_lib_offset+"switch.py",
    mp_lib_offset+"umail.py",
    mp_lib_offset+"tm1640.py",
    # mp_lib_offset+"char8x8.py",
    # all_lib_offset+"mqtt_hello.py",
    all_lib_offset+"feature_power.py",
    all_lib_offset+"msgqueue.py",
    mp_lib_offset+"mqtt_as.py",
    ]
    print("now pushing python library code")
    for c in code:
        print("installing", c)
        os.system("ampy --port %s put %s" % (serial_port,c))

def push_application_code():
    code = [
    "run.py",
    "cfg.py",
    ]
    print("now pushing python application code")
    for c in code:
        print("installing", c)
        os.system("ampy --port %s put %s" % (serial_port,c))

# this runs from the command line
def main():
    while True:
        try:
            cluster_name = sys.argv[1]
        except:
            print("Input cluster toml file name:")
            cluster_name = input()
        try:
            cluster = load_cluster(cluster_name)
            break
        except:
            print("Try again")
    print_sensors(cluster["sensor"])

    print("select one (case insensitive): ", end="")
    sensor_to_make = input().upper()
    print("request = ", sensor_to_make)
    create_cfg(cluster, sensor_to_make) # drops cfg.py file

    # install micropython kernal
    did_we_flash = False
    print("\ninstall micropython? (y,N)")
    ans = input()
    if (ans.upper() == "Y"):
        did_we_flash = True
        print ("\npress and hold O (flat side)\nthen press RST (indent) momentary\nrelease O\nthen press Enter to continue")
        input()
        flasher()
    # install library code
    if did_we_flash == False:
        print("install library code? (y,N)")
        lans = input()
    else:
        lans = "Y"
    if (lans.upper() == "Y"):
        push_library_code()
    # install application code
    if did_we_flash == True or lans.upper() == "Y":
         ans = "Y"
    else:
        print("\ninstall application code? (Y,n)")
        ans = input()
    if (ans.upper() != "N"):
        push_application_code()
    os.system("ampy --port %s ls" % (serial_port,))
    if os.name == 'nt':
        print("\n  putty -serial ", serial_port)
    else:
        print("\n  picocom -b 115200 ", serial_port)
    if (ans.upper() != "N"):
        print("\nCreated [%s:%s] device" % (cluster["cluster_id"],sensor_to_make)) 

if __name__ == "__main__":
    main()
