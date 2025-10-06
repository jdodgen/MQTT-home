# MIT licence copyright 2025 Jim Dodgen
import os 
import time

micropython_bin = "/home/jim/Downloads/ESP32_GENERIC_S2-20250911-v1.26.1.bin"

def flasher():
    os.system("esptool --after no-reset --chip esp32s2 --port /dev/ttyACM0 erase-flash")
    cmd = "esptool --after hard-reset --chip esp32s2 --port /dev/ttyACM0 write-flash -z 0x1000 %s" % (micropython_bin,)
    print(cmd)
    time.sleep(3)
    os.system(cmd)
    time.sleep(5)
