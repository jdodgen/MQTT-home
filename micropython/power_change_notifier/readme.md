# power change notifier

two or more esp32-s2 microcontrolers that communicate. Typically a [utility_power](src/utility_power) and a [generator_power](src/generator_power) device.

this includes micropython code, pictures of the hand wired board as well as scad and stl files to make the enclosure.

The system consists of:
 - 2 or more sensors that publishes MQTT status and subscribes to the other sensor(s).
 - MQTT broker - [mosquitto](https://mosquitto.org/) runs anywhere: I like tiny linux servers.

/etc/mosquitto/mosquitto.conf needs to contain
```
allow_anonymous true
listener 1883
log_dest none
```
Also the broker name needs to be the same subnet.

###  Electrical parts:
### monitors:
 - [ESP32-s2](https://www.wemos.cc/en/latest/s2/s2_mini.html) Mini microcontroler running micropython use the 2MB PSRAM veraion ESP32-S2FN4R2
 - 2V LED 5mm
 - 220 ohm resistor
 - insulated hookup wire
 - 1/4 electrocookie perf board
 - 2 8 pin male header
 - 2 8 pin female header
## simple MQTT server
 - [NanoPi NEO](https://wiki.friendlyelec.com/wiki/index.php/NanoPi_NEO) tiny linux server
 - MicroSD card 8g or larger
 - Cat5+ patch cable
 - USB AC charger with microUSB connector  
### MicroSD Build:
for "NanoPi NEO" w/heatsink enclosure    
 - Download Ubuntu 16.04 NanoPi image

 - Boot and find its IP or local name
 - login user=pi password=pi
 - apt update and upgrade
 - apt install mosquitto and avahi-daemon
 - add home-broker and home_broker.local to /etc/hosts 
configure mosquitto 
```
allow_anonymous true
listener 1883
log_dest none
autosave_interval 0
autosave_on_changes false
```  
Remove microsd save as master
With Win32diskimager save the image
Create sd clones as needed.



 - 
