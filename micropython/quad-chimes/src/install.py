# MIT license copyright 2024,25 Jim Dodgen
# this configures and installs software
# it replaces the cfg.py file each time it runs
# Y N defaults are designed for rapid deployment during development
# usage is: "python3 install.py cluster_example.toml"
# this does as much preprocessing as it can to freeup the microprocessor
cluster_example_toml='''
# this is a toml configuration file see https://toml.io/
# this file is used by install.py to generate device cfg.py files

cluster_id = "your place"  # as in: "/home/your place/Big Generator/power"

[network]
ssid =  "mywifi"
wifi_password = '12345678'

[mqtt_broker]
broker="home-broker.local"  # or where ever your MQTT broker is
ssl = true/false
user = "user"
password = "password"

[email]
to_list = ["foo@bar.com", "bar@foo.com"]
gmail_password = "xxx xxx xxx xxx"
gmail_user = "??@gmail.com"
'''

import os
from pathlib import Path
import datetime
import tomllib
import sys

###### modify these as needed ######
mp_lib_offset="../../library/"  # micropython specific
all_lib_offset="../../../library/" # both linux and micropython
cluster_lib = str(Path.home())+"/Dropbox/wip/pcn_clusters"

if os.name == 'nt':
    serial_port = "COM3"
else: # linux
    serial_port = "/dev/ttyACM0"
print("Device on:", serial_port)

# to have imports from libraries we need to do this:
# Get the absolute path of the current script's directory
# Add the parent directory to sys.path
# In this example, if main.py is in 'project/', this adds 'project/'
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, all_lib_offset))
import feature_power # located in all_lib_offset
import feature_quad_chimes
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
            return cluster
                # print(cluster)
    except FileNotFoundError:
        print("Error: ",cluster_toml," File not found")
        sys.exit()
    except tomllib.TOMLDecodeError as e:
        print("Error: Invalid TOML format in {file_path}: {e}")
        sys.exit()

# def print_sensors(devices):
    # device_keys = list(devices.keys())
    # device_keys.sort()
    # for key in device_keys:
        # #print("sensor key=", key)
        # if len(key) != 1:
            # print("id [%s] mist be a single letter or number" % (key, ))
        # try:
            # desc =sensors[key]["desc"]
        # except:
            # desc=""
        # print("%s) %s" % (key, desc))
        # if(('+' in desc) or ('/' in desc) or ('+' in key) or ('/' in key)):
            # print("\nERROR: future topic  [%s][%s] contains a / or +,  MQTT reserved fix in toml file\n" % (key,desc,))
            # sys.exit()

class create_cfg:
    def __init__(self, cluster):
        self.cluster = cluster
        self.payload = ""
        self.location = "nowhere"
        self.get_location()
        self.power_feature = feature_power.feature(self.cluster["cluster_id"], location=self.location)   # publisher
        print(self.power_feature.topic())
        self.quad_chimes_feature = feature_quad_chimes.feature(self.cluster["cluster_id"], location=self.location, publish=True)
        print(self.quad_chimes_feature.topic())
        self.get_button_chime()
        self.email_addresses()
        self.write_cfg()

    def get_location(self):
        ndx=0
        locations = self.cluster["locations"]
        for loc in locations:
            ndx += 1
            print("%s) %s" % (str(ndx), loc,))
        print("select one (case insensitive): ", end="")
        loc_selected = input().upper()
        self.location = locations[int(loc_selected)-1]
        print("Location:", loc_selected, self.location)

    def get_button_chime(self):
        print("Button publishes:")
        print("1) Westminster")
        print("2) Ding dong")
        print("3) Ding ding")
        print("4) All three")
        print("select one (case insensitive): ", end="")
        chime_selected = input().upper()
        #print("chime_selected = ", chime_selected)
        if (chime_selected == "1"):
            self.payload = self.quad_chimes_feature.payload_westminster()
        elif (chime_selected == "2"):
            self.payload = self.quad_chimes_feature.payload_ding_dong()
        elif (chime_selected == "3"):
            self.payload = self.quad_chimes_feature.payload_ding_ding()
        elif (chime_selected == "4"):
           self.payload = self.quad_chimes_feature.payload_three_chimes()
        else:
            print("invalid responce")
        print("Chime selected", self.payload)

    def email_addresses(self):
        self.cc_string = ''
        for addr in self.cluster["email"]["to_list"]:
            self.cc_string += "<%s>," % (addr,)
        self.cc_string = self.cc_string.rstrip(",")
        print(self.cc_string)
        return self.cc_string

# this is the cfg.py template uses % to pass in stuff
    def write_cfg(self):
        cfg_template = """
# MIT license copyright 2024, 2025 Jim Dodgen
# this cfg.py was created by: install.py
# Date: %s
# MAKE YOUR CHANGES IN install.py
#
led_gpio          = 3  # optional
onboard_led_gpio  = 15 # built in BLUE led
button_pin        = 12  # D8
play_all_pin      = 35  # D1
ding_dong_pin     = 33  # D2
ding_ding_pin     = 18  # D3
westminster_pin   = 16  # D4

time_to_trigger = 1  # how long to hold down for a chime
#
#
# wifi: IoT or guest network recommended
ssid="%s"
wifi_password = "%s"
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
# a python list of one or more email addresses ["9095551212@tmomail.net", "you@gmail.com"]
send_messages_to = %s # a python list


PCN_publish_power = "%s"
publish_button = "%s"
publish_button_payload = "%s"
cluster_id = "%s"
send_email =  %s
location = "%s"
"""
        now = datetime.datetime.now()
        cfg_text =  cfg_template % (now.strftime("%Y-%m-%d %H:%M:%S"),
            self.cluster["network"]["ssid"],
            self.cluster["network"]["wifi_password"],
            self.cluster["mqtt_broker"]["broker"],
            self.cluster["mqtt_broker"]["ssl"],
            self.cluster["mqtt_broker"]["user"],
            self.cluster["mqtt_broker"]["password"],
            self.cluster["email"]["to_list"],
            self.cluster["email"]["gmail_password"],
            self.cluster["email"]["gmail_user"],
            self.cc_string,
            self.cluster["email"]["to_list"],
            self.power_feature.topic(),
            self.quad_chimes_feature.topic(),
            self.payload,
            self.cluster["cluster_id"],
            self.cluster["send_email"],
            self.location,
            )
        #print("[%s][%s] [%s]\n%s [%s][%s]\n" % (ssid, wifi_password, broker, to_list,
        #   gmail_password, gmail_user ))
        with open('cfg.py', 'w') as f:
            f.write(cfg_text)
        print("created cfg.py")

def flash_micropython():
    os.system("esptool.py --port /dev/ttyACM0 erase_flash")
    os.system("esptool.py --chip esp32s2 --port /dev/ttyACM0 write_flash -z 0x1000 ESP32_GENERIC_S2-20250415-v1.25.0.bin")

def push_library_code():
    code = [
    mp_lib_offset+"main.py",
    mp_lib_offset+"boot.py",
    mp_lib_offset+"uuid.py",
    mp_lib_offset+"alert_handler.py",
    mp_lib_offset+"button.py",
    mp_lib_offset+"umail.py",
    mp_lib_offset+"mqtt_as.py",
    all_lib_offset+"mqtt_hello.py",
    all_lib_offset+"feature_quad_chimes.py",
    all_lib_offset+"feature_power.py",
    all_lib_offset+"msgqueue.py",
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

    create_cfg(cluster) # drops cfg.py file

    # install micropython kernal
    did_we_flash = False
    print ("press and hold O (flat side)\nthen press RST (indent) momentary\nrelease O\nto allow flashing micropython")
    print("install micropython? (y,N)")
    ans = input()
    if (ans.upper() == "Y"):
        did_we_flash = True
        flash_micropython()
        print("\npress RST on esp32-s2 to reset (in the indent) then press Enter to continue")
        input()
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

if __name__ == "__main__":
    main()
