# instaltion of micropython as well as LED_pizo_button code
# MIT Licence Copyright Jim Dodgen 2024

import os
print("""
Press AND HOLD the button labelled BOOT or 0 (ZERO),
then press the RESET button (notched area), then release the BOOT button,
and it should appear as a serial device.
""")

micropython = "../ESP32_GENERIC_S2-20240105-v1.22.1.bin" # change this 

config_boilerplate = '''
# NOTE mqtt_cfg.py import is generated by this file, install.py
# it must drop a python3 compatable file that is imported in the system
# so make changes here
#
'''

cfg=None
while not cfg :
    print("which WiFi? (((T)est or (P)roduction")
    wifi = input().upper()
    print("[%s]" % (wifi,))

    if wifi == "T":
        cfg = config_boilerplate+'''
ssid = 'testwifi'
wifi_pw = 'xxxxx'
server = 'home-broker.local'   # or whate ever your broker name is
'''
    elif wifi == 'P':
        cfg = config_boilerplate+'''
ssid = 'JEDguest'
wifi_pw = '9098673852'
server = 'home-broker.local'
'''
with open("mqtt_cfg.py", "w") as f:
    f.write(cfg)

print("install micropython? (Y,n)")
ans = input()
if (ans.upper() != "N"):
    os.system("esptool.py --port /dev/ttyACM0 erase_flash")
    os.system("esptool.py --chip esp32s2 --port /dev/ttyACM0 write_flash -z 0x1000 "+micropython)
    print("Press RST (button in notched area)")

code = [
"../../library/main.py",
"../../library/boot.py",
"../../library/uuid.py",
"../../library/mqtt_as.py",
"../../../library/feature_alert.py",
"../../../library/feature_button.py",
"../../../library/mqtt_hello.py",
"run.py",
"water_valve.py",
"cfg.py",
"universal_machine.py",
"universal_mqtt_as.py",
"mqtt_cfg.py",
]
#ans = input()
os.system("pwd")
for c in code:
    print("installing [%s]" % (c,))
    os.system("ampy --port /dev/ttyACM0 put "+c)

os.system("ampy --port /dev/ttyACM0 ls")

os.system("picocom -b 115200 /dev/ttyACM0")
