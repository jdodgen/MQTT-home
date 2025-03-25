# MIT license copyright 2024 Jim Dodgen
import os
import datetime
import json

# this configures and installs software
# it replaces the cfg.py file each time it runs
# Y N defaults are designed for rapid deployment during development 

# change wifi and message list to match your environment
mp_lib_offset="../../../library/"
all_lib_offset="../../../../library/"

####
#### many devices version
####
JEDguest=False
mtn1=True
example=False
###


    cluster_id = "2Profs"
    ssid =  "JEDguest"
    wifi_password = '9098673852'
    broker="home-broker.local" 
    to_list = '["9097472800@tmomail.net", "jim@dodgen.us"]'
    gmail_password = "xdom zveb qytq snms" # gmail generates this I can change it in the future
    gmail_user = "notifygenerator@gmail.com"
    cluster_of_devices = ["Genrac","Edison"]

    cluster_id = "2Profs"
    ssid =  "MTN1" 
    wifi_password = 'Wewant$ecureWiFi'
    broker="home-broker.local"  #'home-broker.local'
    to_list = ["9097472800@tmomail.net", "jim@dodgen.us", ] #"power@2profs.net", ]'
    gmail_password = "xdom zveb qytq snms" # gmail generates this I can change it in the future
    gmail_user = "notifygenerator@gmail.com"
    cluster_of_devices = ["Big Generator", "Utility Edison", "solar_batteries"]

# these are extracts of above
devices_we_subscribe_to = []
publisher = ""

i=1
for device in(cluster_of_devices):
    print("%s) %s" % (i,device))
    i += 1
print("select one: ", end="")
req = input()
publisher_ndx=int(req)-1
print(cluster_of_devices[publisher_ndx])
publish_to = cluster_of_devices[publisher_ndx]
device_index = {}
i=0
out=0
publish_cycles_without_a_message =[]
got_other_message = []
have_we_sent_power_is_down_email  = []
start_time = []
for device in(cluster_of_devices):
    if i == publisher_ndx:
        publisher = cluster_of_devices[publisher_ndx]
    else:
        devices_we_subscribe_to.append(device)
        device_index[device] = out
        publish_cycles_without_a_message.append(0)
        got_other_message.append(False)
        have_we_sent_power_is_down_email.append(False)
        start_time.append(False)
        out += 1
    print("%s) %s" % (i,device))
    i += 1
print(devices_we_subscribe_to)
################### end of many devices version


print("\nflashing ssid[%s] device[%s]\n" % (ssid, publish_to,))

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
server = '%s'
#
# a python list of one or more email addresses ["9095551212@tmomail.net", "you@gmail.com"]
send_messages_to = %s
# 
# gmail account to send emails through  
#
gmail_password = "%s" # gmail generates this and it can change it in the future
gmail_user = "%s"

publish = "%s"
devices_we_subscribe_to = %s
device_index = %s
publish_cycles_without_a_message = %s
have_we_sent_power_is_down_email = %s
got_other_message = %s
start_time = %s
publisher = "%s"
cluster_id = "%s"
"""
print("creating cfg.py")
now = datetime.datetime.now()
cfg_text =  cfg_template % (now.strftime("%Y-%m-%d %H:%M:%S"), 
    ssid, wifi_password, broker, to_list,
    gmail_password, gmail_user, publish_to,
    devices_we_subscribe_to, device_index, publish_cycles_without_a_message, 
    have_we_sent_power_is_down_email, got_other_message,start_time,
    publisher,cluster_id)
#print("[%s][%s] [%s]\n%s [%s][%s]\n" % (ssid, wifi_password, broker, to_list,
#   gmail_password, gmail_user ))
with open('cfg.py', 'w') as f:
    f.write(cfg_text) 

print ("press and hold O\nthen press R momentary\nrelease O\nto allow flashing micropython")
print("install micropython? (y,N)")
ans = input()
if (ans.upper() == "Y"):
    os.system("esptool.py --port /dev/ttyACM0 erase_flash")
    os.system("esptool.py --chip esp32s2 --port /dev/ttyACM0 write_flash -z 0x1000 ../ESP32_GENERIC_S2-20241129-v1.24.1.bin")
    print("\npress R on esp32-s2 to reset")
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
    all_lib_offset+"mqtt_hello.py",
    all_lib_offset+"feature_power.py",
    mp_lib_offset+"mqtt_as.py",  # testing
    ]
    print("now pushing python support code")
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

print("cfg.py created")
os.system("ampy --port /dev/ttyACM0 put cfg.py")
print("\ncurrent contents of flash")
os.system("ampy --port /dev/ttyACM0 ls")
print("\n  picocom -b 115200 /dev/ttyACM0")
