# MIT license copyright 2024,2025 Jim Dodgen
import os
import datetime
import json

# this configures and installs software
# it replaces the cfg.py file each time it runs
# Y N defaults are designed for rapid deployment during development 
# 

# change wifi and message list to match your environment
mp_lib_offset="../../../library/"
all_lib_offset="../../../../library/"

s_a = "Generator"
s_b = "Utility"

this_system = "a"  

if (this_system == "a"):
    publish_to = s_a
    subscribe_from = s_b
else:
    publish_to = s_b
    subscribe_from = s_a




jd=False
sn=True
example=False
if (example):
    ssid =  "???" 
    wifi_password = '????????'
    broker='home-broker.local'
    to_list = '["youremail@gmail.com", "a@b.com"]'
    gmail_password = "vvvv vvvv vvvv vvvv" # gmail generates this I can change it in the future
    gmail_user = "????@gmail.com"
    # see https://medium.com/@studentofbharat/send-mail-using-python-code-9ab3b1d146ef
elif (jd):
    ssid =  "sadsadssds" 
    wifi_password = 'asasdasdasd'
    broker="home-broker.local" 
    to_list = '["dsaasdasd@tmomail.net", "asda@asdasd.com"]'
    gmail_password = "eeee eeee eeee eeee" # gmail generates this I can change it in the future
    gmail_user = "asdasdasdasd@gmail.com"
elif (sn):
    ssid =  "" 
    wifi_password = 'Wewant$'
    broker=""  #'home-broker.local'
    to_list = '["", "", ""]'   # email/txt addresses
    gmail_password = "" # gmail generates this I can change it in the future
    gmail_user = ""

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
start_delay=10
number_of_seconds_to_wait=60
server = '%s'
#
# a python list of one or more email addresses ["9095551212@tmomail.net", "you@gmail.com"]
send_messages_to = %s
# 
# gmail account to send emails through  
#
gmail_password = "%s" # gmail generates this I can change it in the future
gmail_user = "%s"
# gen cost to run per hour https://generatorsupercenter.com/how-much-do-generators-cost-to-run/
cost_to_run = 1.88  # in any currency 
publish_to = "%s"
subscribe_from = "%s"
"""
now = datetime.datetime.now()
with open('cfg.py', 'w') as f:
    f.write(cfg_template % (now.strftime("%Y-%m-%d %H:%M:%S"), 
    ssid, wifi_password, broker, to_list,
    gmail_password, gmail_user,
    publish_to, subscribe_from )) #json.dumps(to_list)))
print ("press and hold O the press R momentary release O to allow flash, to install micropython")
print("install micropython? (y,N)")
ans = input()
if (ans.upper() == "Y"):
    os.system("esptool.py --port /dev/ttyACM0 erase_flash")
    os.system("esptool.py --chip esp32s2 --port /dev/ttyACM0 write_flash -z 0x1000 ../ESP32_GENERIC_S2-20241129-v1.24.1.bin")
    print("press R on esp32-s2 to reset(Enter)")
    input()

print("install library code? (y,N)")
ans = input()
if (ans.upper() == "Y"):
    code = [
    mp_lib_offset+"main.py",
    mp_lib_offset+"mqtt_as.py",
    mp_lib_offset+"boot.py",
    mp_lib_offset+"uuid.py",
    mp_lib_offset+"alert_handler.py",
    mp_lib_offset+"umail.py",
    all_lib_offset+"mqtt_hello.py",
    all_lib_offset+"feature_power.py",
    ]
    print("now pushing python support code")
    for c in code:
        print("installing", c)
        os.system("ampy --port /dev/ttyACM0 put "+c)

print("install application code? (Y,n)")
ans = input()
if (ans.upper() != "N"):
    code = [
    "cfg.py",
    "run.py",
    ]
    print("now pushing python application code")
    for c in code:
        print("installing", c)
        os.system("ampy --port /dev/ttyACM0 put "+c)

print("\ncurrent contents of flash")
os.system("ampy --port /dev/ttyACM0 ls")
print("\npicocom -b 115200 /dev/ttyACM0")
