# MIT license copyright 2025 Jim Dodgen
import os

mp_lib_offset="../../library/"
all_lib_offset="../../../library/"
test_main_offset="test_main/"

print ("press and hold O (flat side)\nthen press R (indent) momentary\nrelease O\nto allow flashing micropython")
print("install micropython? (y,N)")
ans = input()
if (ans.upper() == "Y"):
    os.system("esptool.py --port /dev/ttyACM0 erase_flash")
    os.system("esptool.py --chip esp32s2 --port /dev/ttyACM0 write_flash -z 0x1000 ESP32_GENERIC_S2-20250415-v1.25.0.bin")
    print("\npress R on esp32-s2 to reset (in the indent)")
    input()

code = [test_main_offset+"main.py", mp_lib_offset+"boot.py",]
print("now pushing python library code")
for c in code:
    print("installing", c)
        os.system("ampy --port /dev/ttyACM0 put "+c)

code = ["test.py",]
print("now pushing python application code")
for c in code:
    print("installing", c)
    os.system("ampy --port /dev/ttyACM0 put "+c)

print("\ncurrent contents of flash")
os.system("ampy --port /dev/ttyACM0 ls")
print("\n  picocom -b 115200 /dev/ttyACM0   ")
