# MIT license copyright 2024 Jim Dodgen
# this is a fresh port into git and will need changes to run
# 
import os
import datetime
import json

# this configures and installs software
# it replaces the cfg.py file each time it runs
# Y N defalts are designed for development 

# change wifi and message list to match your environment

ssid = 'guest' # guest wifi
wifi_password = 'foo'
send_messages_to = ["???@tmomail.net", "XXX@YYYYY.foo"]  # note a python list only

# ceja's
#ssid = '??' 
#wifi_password = '?'
#send_messages_to = '["9097472800@tmomail.net", "m82002a@gmail.com"]'  # note a python list inside quotes
#
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

number_of_seconds_to_wait=60
server = 'home-broker.local'
#
# a python list of one or more email addreses ["9095551212@tmomail.net", "you@gmail.com"]
send_messages_to = %s
# 
# gmail account to send emails through  
# see https://medium.com/@studentofbharat/send-mail-using-python-code-9ab3b1d146ef
#
gmail_password = "xdom zveb qytq snms" # gmail generates this I can change it in the future
gmail_user = "notifygenerator@gmail.com"
# gen cost to run per hour https://generatorsupercenter.com/how-much-do-generators-cost-to-run/
cost_to_run = 1.88  # in any currency 
"""
now = datetime.datetime.now()
with open('cfg.py', 'w') as f:
    f.write(cfg_template % (now.strftime("%Y-%m-%d %H:%M:%S"), ssid, wifi_password, json.dumps(send_messages_to)))

print("install micropython? (y,N)")
ans = input()
if (ans.upper() == "Y"):
    os.system("esptool.py --port /dev/ttyACM0 erase_flash")
    os.system("esptool.py --chip esp32s2 --port /dev/ttyACM0 write_flash -z 0x1000 ../../ESP32_GENERIC_S2-20240105-v1.22.1.bin")
    print("press R on esp32-s2 to reset(Enter)")
    input()

print("install library code? (y,N)")
ans = input()
if (ans.upper() == "Y"):
    code = [
    "../../library/main.py",
    "../../library/mqtt_as.py",
    "../../library/boot.py",
    "../../library/uuid.py",
    "../../library/alert_handler.py",
    "../../library/umail.py",
    "../../../library/mqtt_hello.py",
    "../../../library/feature_power.py",
    ]
    print("now pushing python support code")
    for c in code:
        print("installing", c)
        os.system("ampy --port /dev/ttyACM0 put "+c)

print("press R to reset\ninstall IoD code? (Y,n)")
ans = input()
if (ans.upper() != "N"):
    code = [
    "run.py",
    "cfg.py",
    ]
    print("now pushing python IoD code")
    for c in code:
        print("installing", c)
        os.system("ampy --port /dev/ttyACM0 put "+c)

    os.system("ampy --port /dev/ttyACM0 ls")
print("\ncurrent contents of flash")
os.system("ampy --port /dev/ttyACM0 ls")
print("\npicocom -b 115200 /dev/ttyACM0")
