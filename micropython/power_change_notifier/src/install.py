# MIT license copyright 2024,25 Jim Dodgen
# usage is python3 install.py snd the cluster toml file
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
[sensor.1]
id = "G"
desc = "Generator powered outlet" # Typicaly in gally/kitchen in plain sight
email = true  # if false this sensor does not send emails
[sensor.2]
id = "U"
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
'''

import os
import datetime
import tomllib
import sys

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


if len(sys.argv) > 1:
    cluster_toml = sys.argv[1]
else:
    print("testing from vsc")
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

print("select one: ", end="")
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
else:  # these "letters" do not exist in the config but are treated as "soft_tracking"  that is not tracked until first publish
    publish_to = sensor_to_make   # single letter version
    send_email = False
    ssid = cluster["network"]["ssid"]
    wifi_password = cluster["network"]["wifi_password"]


print("bulding a ",publish_to)

#publisher_ndx=int(req)-1
# pre build some lists
device_index = {}
devices_we_subscribe_to = []
#list_of_other_topics = []
publish_cycles_without_a_message =[]
got_other_message = []
have_we_sent_power_is_down_email  = []
start_time = []
#
# out=0
# i=0
# for key in sensor_keys:
    # if i == publisher_ndx:
        # pass
    # else:
        # name =sensors[key]["name"]
        # devices_we_subscribe_to.append(name)
        # #list_of_other_topics.append(feature_power.feature(cfg.cluster_id+"/"+dev, subscribe=True).topic())
        # device_index[name] = out
        # publish_cycles_without_a_message.append(0)
        # got_other_message.append(False)
        # have_we_sent_power_is_down_email.append(False)
        # start_time.append(False)
        # out += 1
    # i += 1
# print(devices_we_subscribe_to)

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

# for dev in devices_we_subscribe_to:
    # print("subscribing to:", dev)
    # #other_device_features.append(feature_power.feature(cfg.cluster_id+"/"+dev, subscribe=True))
    # other_device_topics.append(feature_power.feature(cluster["cluster_id"]+"/"+dev, subscribe=True).topic())

#wildcard_subscribe = feature_power.feature(cluster["cluster_id"]+"/+", subscribe=True)
#print(wildcard_subscribe.topic())

hard_tracked_topics = []
soft_tracking = "soft_tracking" # soft tracked sensors are only tracked after first publish and ignored at boot
for key in sensor_keys:
    if soft_tracking in sensors[key]:
        if sensors[key][soft_tracking] == True:
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
#
ssid="%s"
wifi_password = "%s"
#
start_delay=0 # startup delay
number_of_seconds_to_wait=30  # messages published and checked
other_message_threshold=4  # how many number_of_seconds_to_wait to indicate other is down
subscribe_interval = 10 # count of number_of_seconds_to_wait to cause subscribe
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
hard_tracked_topics = %s
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
    hard_tracked_topics)
#print("[%s][%s] [%s]\n%s [%s][%s]\n" % (ssid, wifi_password, broker, to_list,
#   gmail_password, gmail_user ))
with open('cfg.py', 'w') as f:
    f.write(cfg_text)
print("cfg.py created")

did_we_flash = False
print ("press and hold O (flat side)\nthen press R (indent) momentary\nrelease O\nto allow flashing micropython")
print("install micropython? (y,N)")
ans = input()
if (ans.upper() == "Y"):
    did_we_flash = True
    os.system("esptool.py --port /dev/ttyACM0 erase_flash")
    # os.system("esptool.py --chip esp32s2 --port /dev/ttyACM0 write_flash -z 0x1000 ESP32_GENERIC_S2-20241129-v1.24.1.bin")
    os.system("esptool.py --chip esp32s2 --port /dev/ttyACM0 write_flash -z 0x1000 ESP32_GENERIC_S2-20250415-v1.25.0.bin")
    print("\npress R on esp32-s2 to reset (in the indent)")
    input()
if did_we_flash == False:
    print("install library code? (y,N)")
    ans = input()
else:
    ans = "Y"
if (ans.upper() == "Y"):
    code = [
    mp_lib_offset+"main.py",
    #mp_lib_offset+"mqtt_as.py",
    mp_lib_offset+"boot.py",
    mp_lib_offset+"uuid.py",
    mp_lib_offset+"alert_handler.py",
    mp_lib_offset+"umail.py",
    #all_lib_offset+"mqtt_hello.py",
    all_lib_offset+"feature_power.py",
    all_lib_offset+"msgqueue.py",
    #mp_lib_offset+"mqtt_support.py",
    #mp_lib_offset+"asimple.py",
    #mp_lib_offset+"arobust.py",
    mp_lib_offset+"mqtt_as.py",
    ]
    print("now pushing python library code")
    for c in code:
        print("installing", c)
        os.system("ampy --port /dev/ttyACM0 put "+c)
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

os.system("ampy --port /dev/ttyACM0 put cfg.py")
print("\ncurrent contents of flash")
os.system("ampy --port /dev/ttyACM0 ls")
print("\n  picocom -b 115200 /dev/ttyACM0")
