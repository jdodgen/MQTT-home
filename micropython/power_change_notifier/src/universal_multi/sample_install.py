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

systemA = "generator"
systemB = "Utility"
print("A[%s]\nB[%s]\n(A or B)" % (systemA,systemB,))
this_system = input()
if (this_system.upper() == "A"):  
    publish_to= systemA      #  systemA publishes status every N minutes
    subscribe_from = systemB  #  systemA subscribes to systemB published status
else:
    publish_to = systemB      # reversed
    subscribe_from = systemA

####
#### many devices version
####
cluster_of_devices = [systemA,systemB,"2battery"]
# these are extracts of above
devices_we_subscribe_to = []
publisher = ""

i=1

for device in(cluster_of_devices):
    print("%s) %s" % (i,device))
    i += 1
print("select one: ", end="")
req = input()
ndx=int(req)-1
print(cluster_of_devices[ndx])
i=0
for device in(cluster_of_devices):
    if i == ndx:
        publisher = cluster_of_devices[ndx]
    else:
        devices_we_subscribe_to.append(cluster_of_devices[i])
    print("%s) %s" % (i,device))
    i += 1
print(devices_we_subscribe_to)

print("flashing [%s]\n" % (publish_to,))

JEDguest=False
mtn1=True
example=False
if (example):
    ssid =  "???" 
    wifi_password = '????????'
    broker='home-broker.local'
    to_list = '["youremail@gmail.com", "a@b.com"]'
    gmail_password = "vvvv vvvv vvvv vvvv" # gmail generates this I can change it in the future
    gmail_user = "????@gmail.com"
    # see https://medium.com/@studentofbharat/send-mail-using-python-code-9ab3b1d146ef
elif (xx):
    ssid =  "xx"
    wifi_password = 'xx'
    broker="home-broker.local" 
    to_list = '["123", "foo@dot.com"]'
    gmail_password = "xxx xxx xxx xxx xxx" # gmail generates this I can change it in the future
    gmail_user = "your@gmail.com"

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
subscribe = "%s"
devices_we_subscribe_to = %s
publisher = "%s"
"""
print("creating cfg.py")
now = datetime.datetime.now()
cfg_text =  cfg_template % (now.strftime("%Y-%m-%d %H:%M:%S"), 
    ssid, wifi_password, broker, to_list,
    gmail_password, gmail_user, publish_to, subscribe_from ,
    devices_we_subscribe_to, publisher)
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
