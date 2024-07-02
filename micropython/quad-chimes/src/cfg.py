
# MIT license copyright 2024 Jim Dodgen
# this cfg.py was created by: install.py
# Date: 2024-03-24 12:18:25 
# MAKE YOUR CHANGES IN install.py
#
# chime chip:  this was built for this:
# https://www.futurlec.com/Others/HK522.shtml

play_all_pin          = 35  # D1
ding_dong_pin         = 33  # D2
ding_ding_pin         = 16  # D3
westminster_pin       = 18  # D4
button_pin            = 12  # D8

name = "door_bell"
time_to_trigger = 0.5  # how long to hold down for a chime

# user specific stuff:
ssid="JEDguest"
wifi_password = "9098673852"
# note: It is best to use firewalled router/wifi for IoT things
server = "home-broker.local"
