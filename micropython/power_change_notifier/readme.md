# Power Change Notifier (PCN)

Two or more esp32-s2 microcontrolers that communicate via [MQTT](https://en.wikipedia.org/wiki/MQTT). Typically monitoring electric company power and a backup generator, can also include things like [UPS](https://en.wikipedia.org/wiki/Uninterruptible_power_supply)'s, solar systems, or other things. 

This system includes: micropython code, Specifications for the prototype board verson, [scad](https://openscad.org/) and stl files to 3d print the enclosures (currently two modifiable types).

The system consists of:
 - 2 or more PCN sensors.They each "publish" a "life" status to MQTT. and "subscribe" to all the other sensors. They control both the onboard LED as well as a GPIO connected LED. Email is used to report startup, a power loss and power restored.
 - A MQTT Broker which can be on your LAN or a service in the cloud.

## Development Hardware:
ESP32-S2 4MB FLASH 2MB PSRAM
### Processor:
 - [ESP32-s2](https://www.wemos.cc/en/latest/s2/s2_mini.html) "Mini" microcontroler ESP32-S2FN4R2 or better.
### Breadboard 3D case version 
 - 2V LED 5mm
 - 220 ohm resistor
 - insulated hookup wire
 - 1/4 electrocookie perf board
 - 2 8-pin male headers
 - 2 8-pin female headers
### Simple 3D case version
 - just the ESP32-s2 
### Also if you want to run a simple local MQTT server
see [Simple MQTT Broker](https://github.com/jdodgen/MQTT-home/tree/main/linux/home-broker/baby_home_broker)



 - 
