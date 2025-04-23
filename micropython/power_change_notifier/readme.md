# power change notifier

two or more esp32-s2 microcontrolers that communicate. Typically a utility power and a generator. 

this includes micropython code, pictures of the hand wired board as well as scad and stl files to make the enclosure.

The system consists of:
 - 2 or more sensors that publishes MQTT status and subscribes to the other sensor(s).
 - MQTT broker - [mosquitto](https://mosquitto.org/) runs anywhere: [simple MQTT broker](https://github.com/jdodgen/MQTT-home/tree/main/linux/home-broker/baby_home_broker).

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
see [Simple MQTT Broker](https://github.com/jdodgen/MQTT-home/tree/main/linux/home-broker/baby_home_broker)



 - 
