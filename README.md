# MQTT-home
This is a hierarchical development environment used for creation of both micropython and linux "things".  
All comnicating using MQTT messages.
Larger/more complex are using linux on devices like a "Raspbery pi"
smaller are using microcontrollers that support [micropython](https://micropython.org/)

# Current things inside:
linux:   
[home-broker](https://github.com/jdodgen/MQTT-home/tree/main/linux/home-broker)  mqtt,zigbee and wemo server     
[Tankless water heater recirculation system](https://github.com/jdodgen/MQTT-home/tree/main/linux/hot-water-recirc)   
Micropython:   
[Button with LED and buzzer](https://github.com/jdodgen/MQTT-home/tree/main/micropython/LED-Piezo-Button)   
[Motorized Ball Valve controller](https://github.com/jdodgen/MQTT-home/tree/main/micropython/ball_valve_controller)   

# Directory organization
## MQTT-home/Library
Code shared by both micropython and linux
## MQTT-home/linux
Linux IoT, typicaly RPI servers, linux projects live here
## MQTT-home/micropython
Currently ESP32-S2 projects. Anything else using micropython goes here.
### MQTT-home/micropython/library
libray of code specific to micropython devices

# Operational Notes
[home-broker](https://github.com/jdodgen/MQTT-home/tree/main/linux/home-broker) runs the show:    
It integrates [fauxmo](https://github.com/n8henrie/fauxmo), [zigbee2mqtt](https://github.com/Koenkk/zigbee2mqtt), [mosquitto](https://github.com/eclipse/mosquitto) (MQTT Broker).  
It has a protocol to let the IP devices report their configurationsimular to how z2m works  
Zigbee and IP devices are stored in a sqlite3 database in a common format.  
it MQTT publishes a compressed JSON of all devices and features. for use of other MQTT devices.   
# It is only a "configuration manager" 
its job is to only collect store and distibute the configuration that is all.
Other automation systems use configuration file for the MQTT messages comunicate with "things".





