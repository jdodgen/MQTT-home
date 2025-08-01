# MIT license copyright 2024,25 Jim Dodgen
# usage is python3 install.py and the cluster toml file
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

[sensor]
#  do not use slashes "/" or "+" in the "name". It messes with the MQTT wild cards
#  email = true means that the sensor sends emails when sensors lost and found
[sensor.G]
desc = "Generator powered outlet" # Typically in gally/kitchen in plain sight
email = true  # if false this sensor does not send emails
[sensor.U]
desc = "Utility power company"
email = true
[sensor.3]
id = "S"
soft_tracking = true  # not monitored at boot only after a publish
name = "solar_batteries"
email = false
[sensor.3]
id = "R"
desc = "Offsite monitor"
email = false
ssid = "otherwifi"
wifi_password = "otherpw"
[sensor.E]
desc = "passive watcher"
monitor_only = true  # this only subscribes and does NOT publish a status. it is soft_tracking by default
send_email = true
'''

import os
import datetime
import tomllib
import sys

# change these as needed
if os.name == 'nt':
	serial_port = "COM3"
	cluster_lib = "C:\Users\jim\Dropbox\wip\pcn_clusters"
else: # linux
	serial_port = "/dev/ttyACM0"
	cluster_lib = "~jim/Dropbox\wip\pcn_clusters"
	
print("Device on:", serial_port)
# Get the absolute path of the current script's directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Add the parent directory to sys.path
# In this example, if main.py is in 'project/', this adds 'project/'
sys.path.append(os.path.join(current_dir, '../../../library/'))
import feature_power

# this configures and installs software
# it replaces the cfg.py file each time it runs
# Y N defaults are designed for rapid deployment during development

mp_lib_offset="../../library/"
all_lib_offset="../../../library/"

def optional_value(where, val, check=True, default=False):
    if val in where:
        if where[val] == check:
            return check
    return default

if len(sys.argv) > 1:
    cluster_toml = cluster_lib+"/"+sys.argv[1]
else:
    print("testing from current directory")
    cluster_toml = "cluster-example.toml"  # test cluster
try:
    with open(cluster_toml, 'rb') as toml_file:
            cluster = tomllib.load(toml_file)
            # print(cluster)
except FileNotFoundError:
    print("Error: ",cluster_toml," File not found")
    sys.exit()
except tomllib.TOMLDecodeError as e:
    print("Error: Invalid TOML format in {file_path}: {e}")
    sys.exit()


# build cc: string
cc_string = ''
for addr in cluster["email"]["to_list"]:
    cc_string += "<%s>," % (addr,)
cc_string = cc_string.rstrip(",")
print(cc_string)

sensors = cluster["sensor"]
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

print("select one case insensitive: ", end="")
sensor_to_make = input().upper()
print("request = ", sensor_to_make)
if sensor_to_make in sensors:
    if "desc" in sensors[sensor_to_make] and len(sensors[sensor_to_make]['desc']) > 0:
        publish_to = sensor_to_make+" "+sensors[sensor_to_make]['desc']
    else:
        publish_to = sensor_to_make   # single letter version
    print("publish_to [%s]" %  (publish_to,))
    if "send_email" in sensors[sensor_to_make] and sensors[sensor_to_make]["send_email"] == True:
        send_email = True
    else:
        send_email = False
    if "ssid" in sensors[sensor_to_make]:
        wifi_password = sensors[sensor_to_make]["wifi_password"]
        ssid = sensors[sensor_to_make]["ssid"]
    else: # take default
        ssid = cluster["network"]["ssid"]
        wifi_password = cluster["network"]["wifi_password"]
    if optional_value(sensors[key], "monitor_only") == True:
        monitor_only = True
    else:
        monitor_only = False

    switch = optional_value(sensors[sensor_to_make], "switch")
    switch_type =  optional_value(sensors[sensor_to_make], "switch_type", check="NC", default="NO")

else:  # these "letters" do not exist in the config but are treated as "soft_tracking"  that is not tracked until first publish
    publish_to = sensor_to_make   # single letter version
    send_email = False
    ssid = cluster["network"]["ssid"]
    wifi_password = cluster["network"]["wifi_password"]
print("ssid[%s] pw[%s]" % (ssid, wifi_password,))


#print("bulding a ",publish_to)

#publisher_ndx=int(req)-1
# pre build some lists
device_index = {}
devices_we_subscribe_to = []
#list_of_other_topics = []
publish_cycles_without_a_message =[]
got_other_message = []
have_we_sent_power_is_down_email  = []
start_time = []

def make_topic_cluster_pub(letter):
    if letter in sensors:
        if "desc" in sensors[letter]:
            desc = sensors[letter]["desc"]
        else:
            desc = ''
    else:
        desc = ''
    if desc == '':
        return cluster["cluster_id"]+"/"+letter
    else:
        return cluster["cluster_id"]+"/"+letter+" "+desc

# build features
our_feature    = feature_power.feature(make_topic_cluster_pub(publish_to), publish=True)   # publisher
print(our_feature.topic())

hard_tracked_topics = [] # these get tracked from boot. others (soft) only after first publish
for key in sensor_keys:
    if optional_value(sensors[key], "soft_tracking") == True or optional_value(sensors[key], "monitor_only") == True:
            continue
    if key != sensor_to_make:  # not tracking self
        hard_tracked_topics.append(feature_power.feature(make_topic_cluster_pub(key), subscribe=True).topic())
print("hard tracked topics", hard_tracked_topics)

print("\nflashing ssid[%s] device[%s]\n" % (ssid, publish_to,))

# this is the cfg.py template uses % to pass in stuff
cfg_template = """
# MIT license copyright 2024, 2025 Jim Dodgen
# this cfg.py was created by: install.py
# Date: %s
# MAKE YOUR CHANGES IN install.py
#
led_gpio = 3  # "D3" on D1-Mini proto card
onboard_led_gpio = 15 # built in BLUE led
switch_gpio = 18 # only used when "switch = True"
#
#wifi: IoT or guest network recomended
ssid="%s"
wifi_password = "%s"
#
#
start_delay=0 # startup delay
number_of_seconds_to_wait=30  # Alive message published and "missing sender search" conducted at this rate
other_message_threshold=4  # how many number_of_seconds_to_wait to indicate other is down
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
cluster_id = "%s"
send_email =  %s
hard_tracked_topics = %s # these get tracked from boot, others only after first publish
monitor_only = %s  # this sensor does not publish status and therefore is not tracked
switch = %s # if true then gpio 18 is tested if off then no publish will be sent
switch_type = "%s" # for "NO or NC defaults to "NO". So when "closed" no "power" publishes are sent
"""
print("creating cfg.py")
now = datetime.datetime.now()
cfg_text =  cfg_template % (now.strftime("%Y-%m-%d %H:%M:%S"),
    ssid,
    wifi_password,
    cluster["mqtt_broker"]["broker"],
    cluster["mqtt_broker"]["ssl"],
    cluster["mqtt_broker"]["user"],
    cluster["mqtt_broker"]["password"],
    cluster["email"]["to_list"],
    cluster["email"]["gmail_password"],
    cluster["email"]["gmail_user"],
    cc_string,
    publish_to,
    cluster["cluster_id"],
    send_email,
    hard_tracked_topics,
    monitor_only,
    switch,
    switch_type)
#print("[%s][%s] [%s]\n%s [%s][%s]\n" % (ssid, wifi_password, broker, to_list,
#   gmail_password, gmail_user ))
with open('cfg.py', 'w') as f:
    f.write(cfg_text)
print("created cfg.py")

# install micropython kernal
did_we_flash = False
print ("press and hold O (flat side)\nthen press RST (indent) momentary\nrelease O\nto allow flashing micropython")
print("install micropython? (y,N)")
ans = input()
if (ans.upper() == "Y"):
    did_we_flash = True
    os.system("esptool.py --port /dev/ttyACM0 erase_flash")
    # os.system("esptool.py --chip esp32s2 --port /dev/ttyACM0 write_flash -z 0x1000 ESP32_GENERIC_S2-20241129-v1.24.1.bin")
    os.system("esptool.py --chip esp32s2 --port /dev/ttyACM0 write_flash -z 0x1000 ESP32_GENERIC_S2-20250415-v1.25.0.bin")
    print("\npress RST on esp32-s2 to reset (in the indent)")
    input()
# install library code
if did_we_flash == False:
    print("install library code? (y,N)")
    ans = input()
else:
    ans = "Y"
if (ans.upper() == "Y"):
    code = [
    mp_lib_offset+"main.py",
    mp_lib_offset+"boot.py",
    mp_lib_offset+"uuid.py",
    mp_lib_offset+"alert_handler.py",
    mp_lib_offset+"switch.py",
    mp_lib_offset+"umail.py",
    #all_lib_offset+"mqtt_hello.py",
    all_lib_offset+"feature_power.py",
    all_lib_offset+"msgqueue.py",
    mp_lib_offset+"mqtt_as.py",
    ]
    print("now pushing python library code")
    for c in code:
        print("installing", c)
        os.system("ampy --port %s put %s" % (serial_port,c))

# install application code
if did_we_flash == False:
    print("\ninstall application code? (Y,n)")
    ans = input()
else:
    ans = "Y"

if (ans.upper() != "N"):
    code = [
    "run.py",
    ]
    print("now pushing python application code")
    for c in code:
        print("installing", c)
        os.system("ampy --port /dev/ttyACM0 put "+c)
print("Installed cfg.py")
os.system("ampy --port /dev/ttyACM0 put cfg.py")
print("\ncurrent contents of flash")
os.system("ampy --port /dev/ttyACM0 ls")
if os.name == 'nt':
	print("\n  putty -serial ", serial_port)
else:
	print("\n  picocom -b 115200 ", serial_port)

