# power change notifier
two esp32-s2 microcontrolers that talk via MQTT and cause emails/sms messages to be sent   
this includes micropython code, pictures of the hand wired board as well as scad and stl files to make the enclosure.

The system consists of:
 - Utility monitor - publishes MQTT status that utility is supplying power
 - Generator monitor - subscribes to the above MQTT and sends emails when the state changes.
 - MQTT broker - if not using home-broker then a small cheap linux with [mosquitto](https://mosquitto.org/). 

/etc/mosquitto/mosquitto.conf needs to contain
```
allow_anonymous true
listener 1883
log_dest none"
```
Also the broker name needs to be the same subnet. In install.py default is "home-broker.local"

###  Electrical parts:
### monitors:
 - [ESP32-s2](https://www.wemos.cc/en/latest/s2/s2_mini.html) Mini microcontroler running micropython use the 2MB PSRAM veraion ESP32-S2FN4R2
 - 3V LED 5mm
 - 220ohm resistor
 - 8mm insulated hookup wire
 - 1/4 electrocookie perf board
 - 2 8 pin male header
 - 2 8 pin female header
### simple MQTT server
 - [NanoPi NEO](https://wiki.friendlyelec.com/wiki/index.php/NanoPi_NEO) tiny linux server
 - MicroSD card 8g or larger
 - Cat5+ patch cable
 - USB AC charger with microUSB connector  
 - 
