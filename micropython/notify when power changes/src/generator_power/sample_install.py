# MIT license copyright 2024 Jim Dodgen
import os
import datetime
import json

# this configures and installs software
# it replaces the cfg.py file each time it runs
# Y N defalts are designed for development 

# change wifi and message list to match your environment
mp_lib_offset="../../../library/"
all_lib_offset="../../../../library/"

ssid = 'xx' 
wifi_password = 'xxx'
to_list = '["???@tmomail.net", "??@foo.com"]'
gmail_password = "aaaa aaaa aaaa aaaa" # gmail generates this I can change it in the future
gmail_user = "???@gmail.com"
# see https://medium.com/@studentofbharat/send-mail-using-python-code-9ab3b1d146ef

# this is the future cfg.py file
cfg_template = """
# MIT license copyright 2024 Jim Dodgen
# this cfg.py was created by: install.py
# Date: %s 
# MAKE YOUR CHANGES IN install.py
#
led_gpio = 3  # "D3" on D1-Mini proto card
#
# best to use firewalled router/wifi for IoT things
ssid="%s"
wifi_password = "%s"
#
start_delay=10
number_of_seconds_to_wait=60
server = 'home-broker.local'
#
# a python list of one or more email addreses ["9095551212@tmomail.net", "you@gmail.com"]
send_messages_to = %s
# 
# gmail account to send emails through  
#
gmail_password = "%s" # gmail generates this I can change it in the future
gmail_user = "%s"
# gen cost to run per hour https://generatorsupercenter.com/how-much-do-generators-cost-to-run/
cost_to_run = 1.88  # in any currency 
"""
now = datetime.datetime.now()
with open('cfg.py', 'w') as f:
    f.write(cfg_template % (now.strftime("%Y-%m-%d %H:%M:%S"), 
    ssid, wifi_password, to_list,
    gmail_password, gmail_user )) #json.dumps(to_list)))

print("install micropython? (y,N)")
ans = input()
if (ans.upper() == "Y"):
    os.system("esptool.py --port /dev/ttyACM0 erase_flash")
    os.system("esptool.py --chip esp32s2 --port /dev/ttyACM0 write_flash -z 0x1000 ../ESP32_GENERIC_S2-20241129-v1.24.1.bin")
    print("press R on esp32-s2 (the indent) to reset\nthen press Enter")
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
    "run.py",
    "cfg.py",
    ]
    print("now pushing python application code")
    for c in code:
        print("installing", c)
        os.system("ampy --port /dev/ttyACM0 put "+c)

    os.system("ampy --port /dev/ttyACM0 ls")
print("\ncurrent contents of flash")
os.system("ampy --port /dev/ttyACM0 ls")
print("\npicocom -b 115200 /dev/ttyACM0")
