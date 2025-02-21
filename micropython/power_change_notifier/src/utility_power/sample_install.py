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

jd=False
sn=True
example=False
if (example):
    ssid =  "???" 
    wifi_password = '????????'
    broker='home-broker.local'
elif (jd):
    ssid =  "xxxxx" 
    wifi_password = 'xxxxxx'
    broker="home-broker.local" 
elif (sn):
    ssid =  "xxxxx" 
    wifi_password = 'xxxxxxx'
    broker='home-broker.local'

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
number_of_cycles_to_run=60 # 4 minutes
server = '%s'
"""

print("[%s][%s] [%s]\n" % (ssid, wifi_password, broker,))
now = datetime.datetime.now()
with open('cfg.py', 'w') as f:
    f.write(cfg_template % (now.strftime("%Y-%m-%d %H:%M:%S"), 
    ssid, wifi_password, broker))
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
    #mp_lib_offset+"mqtt_as.py",
    ]
    print("now pushing python application code")
    for c in code:
        print("installing", c)
        os.system("ampy --port /dev/ttyACM0 put "+c)

print("\ncurrent contents of flash")
os.system("ampy --port /dev/ttyACM0 ls")
print("\npicocom -b 115200 /dev/ttyACM0")
