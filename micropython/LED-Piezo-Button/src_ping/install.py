# install script to
# Push/flash system into MCU and attach console for testing
# MIT License Copyright Jim Dodgen 2024
# customized for LED piezo buzzer
# 
import os 
import datetime
import json
# configuration area:
# 
test_server = ''
test_ssid = ''
test_wifi_password = '' 
#
tty_port = "/dev/ttyACM0" 
mp_lib_offset="../../library/"
all_lib_offset="../../../library/"
#micropython_bin = "/home/jim/Downloads/ESP32_GENERIC_S2-20240105-v1.22.1.bin"
micropython_bin = "/home/jim/Downloads/ESP32_GENERIC_S2-20240602-v1.23.0.bin"
network_json = "../../../network.json"

net = json.load(open(network_json))
server = 'home-broker.local'
ssid = net["ssid]"]
wifi_password = net["password"]
#
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
lib_code = [
    mp_lib_offset+"main.py",
    mp_lib_offset+"mqtt_as.py",
    mp_lib_offset+"boot.py",
    mp_lib_offset+"uuid.py",
    
    all_lib_offset+"mqtt_hello.py",
    all_lib_offset+"feature_button.py",
    all_lib_offset+"feature_alert.py",
]
app_code = [
    "button.py",
    "mqtt_cfg.py",
    "run.py",
    "cfg.py",
]

'''
"../../library/main.py",
"../../library/boot.py",
"../../library/uuid.py",
"../../library/mqtt_as.py",
"../../../library/feature_alert.py",
"../../../library/feature_button.py",
"../../../library/mqtt_hello.py",
"run.py",
"button.py",
"mqtt_cfg.py",
"alert_handler.py",

"universal_machine.py",
"universal_mqtt_as.py",
'''
# 
# raw code below 
#
## reposition if needed
abspath = os.path.abspath(__file__)
files_dir = os.path.dirname(abspath)+"/" 

## os.chdir(dir)
##print("moved here for paths to work: ",dir)
##

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
        cfg = mqtt_cfg_boilerplate % (test_ssid, test_wifi_password, test_server, now,)
    elif wifi == 'S':
        cfg = mqtt_cfg_boilerplate % (ssid, wifi_password,server, now,)
with open(files_dir+"mqtt_cfg.py", "w") as f: 
    f.write(cfg)
##
did_bin=False
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
        did_bin = True
## 

## sending code    
# ans = input("any key, to continue: ") 
print("current directory: ", os.system("pwd"))
if did_bin:
    ans="Y"  
else:    
    ans = input("install library code? (y,N): ")
if (ans.upper() == "Y"):
    for c in lib_code:
        print("installing [%s]" % (c,))
        os.system("ampy --port "+tty_port+" put "+files_dir+c)

for c in app_code:
    print("installing [%s]" % (c,))
    os.system("ampy --port "+tty_port+" put "+files_dir+c)
##
#
os.system("ampy --port "+tty_port+" ls")   # list files
print("\nrunning picocom ctrl a x to exit, 'import run' to test\n")
os.system("picocom -b 115200 "+tty_port)  # test console 
