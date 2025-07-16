# power change notifier

Two or more esp32-s2 microcontrolers that communicate via MQTT. Typically utility power and a generator but can also include things like UPS's, solar, or other monitored things. 

This system includes: micropython code, pictures of the hand wired board, scad and stl files to 3d print the enclosures (currently two types).

The system consists of:
 - 2 or more sensors. Actualy a single could be used to do just an email at boot. They all publishes a MQTT message life status. status and subscribes to and from the sensor(s).
 - MQTT broker - [mosquitto](https://mosquitto.org/) which runs anywhere, example: [simple MQTT broker](https://github.com/jdodgen/MQTT-home/tree/main/linux/home-broker/baby_home_broker).

### Electrical Parts:
### microcontroller :
 - [ESP32-s2](https://www.wemos.cc/en/latest/s2/s2_mini.html) "Mini" microcontroler with 2MB PSRAM version ESP32-S2FN4R2 or better.
### Breadboard 3D case version 
 - 2V LED 5mm
 - 220 ohm resistor
 - insulated hookup wire
 - 1/4 electrocookie perf board
 - 2 8-pin male headers
 - 2 8-pin female headers
### Simple 3D case version
 - just the ESP32-s2 
## Also if you want to run a simple local MQTT server
see [Simple MQTT Broker](https://github.com/jdodgen/MQTT-home/tree/main/linux/home-broker/baby_home_broker)



 - 
