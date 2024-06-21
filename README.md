# MQTT-home
This is a hierarchical development environment used for creation of both micropython and linux things.
# Current things inside:
home-broker the server  
Tankless water heater recirculation system  
button with LED and buzzer  

# Organization
# MQTT-home/Library
Code shared by both micropython and linux
# MQTT-home/linux
Linux IoT, typicaly RPI servers
# MQTT-home/micropython
mostly ESP32-S2 projects
# MQTT-home/micropython/library
libray of code specific to micropython devices

# Notes
[home-broker](https://github.com/jdodgen/MQTT-home/tree/main/linux/home-broker) runs the show:    
It integrates fauxmo, zigbee2mqtt, mosquitto (MQTT Broker).  
It has a protocol to let the IP devices report their configuration.  
Zigbee and IP devices are stored in a sqlite3 database in a common format.  
it publishes a compressed JSON of all devices and features.    
its job is to only collect configuration that all.  





