# install script to
# Push/flash system into MCU and attach console for testing
# MIT License Copyright Jim Dodgen 2024
# 
import os 
import datetime
# configuration area:
server = 'home-broker.local'
ssid = 'JEDguest'
wifi_password = '9098673852'
# 
test_server = ''
test_ssid = ''
test_wifi_password = '' 
#
tty_port = "/dev/ttyACM0" 
micropython_bin = "/home/jim/Downloads/ESP32_GENERIC_S2-20240602-v1.23.0.bin"
# current defaults, no changes required
#
mqtt_cfg_boilerplate = '''
# Generated file, do not make changes here 
# this file,  mqtt_cfg.py was created by "install.py"
# so make any changes in "install.py"
#
ssid = "%s"
wifi_pw = "%s"
server = "%s"
# datetime %s 
'''

#
# list of files being installed
#
code = [
    "../library/main.py",
    "../library/mqtt_as.py",
    "../library/boot.py",
    "../library/uuid.py",
    "../../library/mqtt_hello.py",
    "../../library/feature_button.py",
    "../../library/feature_ding_ding.py",
    "../../library/feature_ding_dong.py",
    "../../library/feature_three_chimes.py",
    "../../library/feature_westminster.py",
]
# 
# raw code below 
#
## write mqtt_cfg,py 
cfg=None
while not cfg :
    now = datetime.datetime.now()
    if test_ssid:
        print("which WiFi? (((T)est or (S)tandard")
        wifi = input().upper()
        print("[%s]" % (wifi,))
    else:
        wifi = "S"
    if wifi == "T":
        cfg = mqtt_cfg_boilerplate % (ssid, wifi_password, server, now,)
    elif wifi == 'S':
        cfg = mqtt_cfg_boilerplate % (ssid, wifi_password,server, now,)
with open("mqtt_cfg.py", "w") as f: 
    f.write(cfg)
##

## micropython bin 
if micropython_bin:
    ans = input("install micropython_bin? (y,N): ")
    if (ans.upper() == "Y"):
        print("""
    MCU needs to be in a flashable state. 
    For ESP32-S2 This works:
    Press AND HOLD the button labelled BOOT or 0 (ZERO),
    then press the RESET button (notched area), then release the BOOT button,
    and it should appear as a serial device ready to flash
    """)
        input("press any key to flash: ")
        os.system("esptool.py --port /dev/ttyACM0 erase_flash")
        os.system("esptool.py --chip esp32s2 --port /dev/ttyACM0 write_flash -z 0x1000 "+micropython_bin)
        input("\nPress RST (button in notched area)\npress any key to continue: ")
## 

## sending code      
#ans = input() 
os.system("pwd")
for c in code:
    print("installing [%s]" % (c,))
    os.system("ampy --port "+tty_port+" put "+c)
##
#
os.system("ampy --port "+tty_port+" ls")   # list files
print("\nrunning picocom ctrl a x to exit, 'import run' to test\n")
os.system("picocom -b 115200 "+tty_port)  # test console 