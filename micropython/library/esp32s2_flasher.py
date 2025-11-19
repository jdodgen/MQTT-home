# MIT licence copyright 2025 Jim Dodgen
import os 
import time

micropython_bin = "ESP32_GENERIC_S2-20250911-v1.26.1.bin"
# micropython_bin = "/home/jim/Downloads/ESP32_GENERIC_S2-20250415-v1.25.0.bin"

class flasher:
    def __init__(self, nt, linux): 
        global micropython_bin
        self.micropython_path = None
        if os.name == 'nt':
            self.serial_port = nt
            self.micropython_path = "/Users/jim/Downloads/"+micropython_bin
        else: # linux
            self.serial_port = linux
            self.micropython_path = "/home/jim/Downloads/"+micropython_bin
        print("Device on:", self.serial_port)
         
    def port(self):
        return self.serial_port

    def flash(self):
        os.system("esptool --after no-reset --chip esp32s2 --port %s erase-flash" % (self.serial_port,))
        cmd = "esptool --after hard-reset --chip esp32s2 --port %s write-flash -z 0x1000 %s" % (self.serial_port, self.micropython_path,)
        print(cmd)
        time.sleep(3)
        os.system(cmd)
        time.sleep(5)
