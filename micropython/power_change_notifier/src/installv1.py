# MIT license copyright 2024,25 Jim Dodgen
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

i=1
sensors = cluster["sensor"]
sensor_keys = list(sensors.keys())
sensor_keys.sort()
for key in sensor_keys:
    name =sensors[key]["name"]
    print("%s) %s" % (i,name))
    i += 1
    if(('+' in name) or ('/' in name)):
        print("ERROR: name contains a / or + Both are MQTT reserved")
        sys.exit()

print("select one: ", end="")
req = input()
publish_to = sensors[req]["name"]
if sensors[req]["email"]:
    send_email = True
else:
    send_email =False



print("bulding a ",publish_to)

publisher_ndx=int(req)-1
# pre build some lists
device_index = {}
devices_we_subscribe_to = []
#list_of_other_topics = []
publish_cycles_without_a_message =[]
got_other_message = []
have_we_sent_power_is_down_email  = []
start_time = []
#
out=0
i=0
for key in sensor_keys:
    if i == publisher_ndx:
        pass
    else:
        name =sensors[key]["name"]
        devices_we_subscribe_to.append(name)
        #list_of_other_topics.append(feature_power.feature(cfg.cluster_id+"/"+dev, subscribe=True).topic())
        device_index[name] = out
        publish_cycles_without_a_message.append(0)
        got_other_message.append(False)
        have_we_sent_power_is_down_email.append(False)
        start_time.append(False)
        out += 1
    i += 1
print(devices_we_subscribe_to)

# build features
our_status    = feature_power.feature(cluster["cluster_id"]+"/"+publish_to, publish=True)   # publisher
print(our_status.topic())

#other_device_features = []
#other_device_topics = []
other_device_topics = [our_status.topic(),] # use this to get echo msgs back during testing

for dev in devices_we_subscribe_to:
    print("subscribing to:", dev)
    #other_device_features.append(feature_power.feature(cfg.cluster_id+"/"+dev, subscribe=True))
    other_device_topics.append(feature_power.feature(cluster["cluster_id"]+"/"+dev, subscribe=True).topic())
print("list of others", other_device_topics)
#wildcard_subscribe = feature_power.feature(cluster["cluster_id"]+"/+", subscribe=True)
#print(wildcard_subscribe.topic())

# list_of_other_topics = []
# for dev in devices_we_subscribe_to:
    # print("subscribing to:", dev)
    # other_status.append(feature_power.feature(cfg.cluster_id+"/"+dev, subscribe=True))
    # list_of_others.append(feature_power.feature(cfg.cluster_id+"/"+dev, subscribe=True).topic())
# print("list of others", list_of_others)
################### end of many devices version


print("\nflashing ssid[%s] device[%s]\n" % (cluster["network"]["ssid"], publish_to,))

# this is the cfg.py template uses % to pass in stuff
cfg_template = """
# MIT license copyright 2024, 2025 Jim Dodgen
# this cfg.py was created by: install.py
# Date: %s
# MAKE YOUR CHANGES IN install.py
#
led_gpio = 3  # "D3" on D1-Mini proto card
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
devices_we_subscribe_to = %s
device_index = %s
publish_cycles_without_a_message = %s
have_we_sent_power_is_down_email = %s
got_other_message = %s
start_time = %s
cluster_id = "%s"
send_email =  %s,
"""
print("creating cfg.py")
now = datetime.datetime.now()
cfg_text =  cfg_template % (now.strftime("%Y-%m-%d %H:%M:%S"),
    cluster["network"]["ssid"], cluster["network"]["wifi_password"],
    cluster["mqtt_broker"]["broker"], cluster["mqtt_broker"]["ssl"], cluster["mqtt_broker"]["user"], cluster["mqtt_broker"]["password"],
    cluster["email"]["to_list"],
    cluster["email"]["gmail_password"], cluster["email"]["gmail_user"], cc_string,
    publish_to, devices_we_subscribe_to, device_index, publish_cycles_without_a_message,
    have_we_sent_power_is_down_email, got_other_message,start_time,
    cluster["cluster_id"], send_email)
#print("[%s][%s] [%s]\n%s [%s][%s]\n" % (ssid, wifi_password, broker, to_list,
#   gmail_password, gmail_user ))
with open('cfg.py', 'w') as f:
    f.write(cfg_text)
print("cfg.py created")

print ("press and hold O (flat side)\nthen press R (indent) momentary\nrelease O\nto allow flashing micropython")
print("install micropython? (y,N)")
ans = input()
if (ans.upper() == "Y"):
    os.system("esptool.py --port /dev/ttyACM0 erase_flash")
    # os.system("esptool.py --chip esp32s2 --port /dev/ttyACM0 write_flash -z 0x1000 ESP32_GENERIC_S2-20241129-v1.24.1.bin")
    os.system("esptool.py --chip esp32s2 --port /dev/ttyACM0 write_flash -z 0x1000 ESP32_GENERIC_S2-20250415-v1.25.0.bin")
    print("\npress R on esp32-s2 to reset (in the indent)")
    input()

print("install library code? (y,N)")
ans = input()
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
    mp_lib_offset+"mqtt_support.py",
    mp_lib_offset+"asimple.py",
    mp_lib_offset+"arobust.py",
    ]
    print("now pushing python library code")
    for c in code:
        print("installing", c)
        os.system("ampy --port /dev/ttyACM0 put "+c)

print("\ninstall application code? (Y,n)")
ans = input()
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
