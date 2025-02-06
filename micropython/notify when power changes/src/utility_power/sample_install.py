# MIT license copyright James Dodgen 2025
import os
# this configures and installs software

# change these to match your environment
mp_lib_offset="../../../library/"
all_lib_offset="../../../../library/"

ssid = '' 
wifi_password = ''
to_list = '["????tmomail.net", "xxx@email.com"]'

cfg_template = """
# THIS cfg.py CREATED OR REPLACED BUY install.py
# MAKE YOUR CHANGES IN install.py
#
# we monitor a realy NO and NC COM is going to ground.
led_gpio     = 3      # "D3"  white 
#
# best to have a firewalled off wifi ssid for IoT things
ssid="%s"
wifi_password = "%s"

number_of_cycles_to_run=120
server = 'home-broker.local'

#
# a list of one or more email addresses ["9095551212@tmomail.net", "you@gmail.com"]
to_list = %s
# 
# gmail account to send emails through  see https://medium.com/@studentofbharat/send-mail-using-python-code-9ab3b1d146ef
gmail_password = "xxx xxx xxx xxx" # this can change in the future
gmail_user = "???@gmail.com"
"""

with open('cfg.py', 'w') as f:
    f.write(cfg_template % (ssid, wifi_password, to_list))

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
    "run.py",
    "cfg.py",
    ]

    print("now pushing python IoD code")
    for c in code:
        print("installing", c)
        os.system("ampy --port /dev/ttyACM0 put "+c)
print("\ncurrent contents of flash")
os.system("ampy --port /dev/ttyACM0 ls")
print("\n  picocom -b 115200 /dev/ttyACM0")
