# MQTT-home
This is a "hierarchical development environment" used for creation of both micropython and linux "things". The hierarchy exists so common code can be shared. See: the libraries.    
All communication using MQTT messages.

Larger/more complex are using linux on small devices like a "Raspberry pi"
smaller are using microcontrollers that support [micropython](https://micropython.org/)

# Some things inside:
### linux:         
[home-broker A mqtt,zigbee and wemo server](https://github.com/jdodgen/MQTT-home/tree/main/linux/home-broker)       
[Tankless water heater recirculation system](https://github.com/jdodgen/MQTT-home/tree/main/linux/hot-water-recirc)       
[basicNVR simple low overhead NVR](https://github.com/jdodgen/MQTT-home/tree/main/linux/basicNVR)       
### Micropython:          
[Button with LED and buzzer](https://github.com/jdodgen/MQTT-home/tree/main/micropython/LED-Piezo-Button)         
[Motorized Ball Valve controller](https://github.com/jdodgen/MQTT-home/tree/main/micropython/ball_valve_controller)          

Larger/more complex are using linux on small devices like a "Raspberry pi"
smaller are using microcontrollers that support [micropython](https://micropython.org/)   

# Directory organization
## MQTT-home/Library
Code shared by both micropython and linux
## MQTT-home/linux
Linux IoT, typically RPI servers, linux projects live here
## MQTT-home/micropython
Currently ESP32-S2 projects. Anything else using micropython goes here.
### MQTT-home/micropython/library
library of shared code specific to micropython devices

# Operational Notes
[home-broker](https://github.com/jdodgen/MQTT-home/tree/main/linux/home-broker) runs the show:    
It integrates [fauxmo](https://github.com/n8henrie/fauxmo), [zigbee2mqtt](https://github.com/Koenkk/zigbee2mqtt), [mosquitto](https://github.com/eclipse/mosquitto) (MQTT Broker).  
It has a protocol to let the IP devices report their configuration similar to how z2m works  
Zigbee and IP devices are stored in a sqlite3 database in a common format.  
home-broker publishes a compressed JSON of all devices and features. for use of other MQTT devices.   
Home-broker is only a "configuration manager"



## MQTT-home/micropython
Currently ESP32-S2 projects. Anything else using micropython goes here.
### MQTT-home/micropython/library# MQTT-home
This is a hierarchical development environment used for creation of both micropython and linux "things".  
All comnicating using MQTT messages.
Larger/more complex are using linux on devices like a "Raspbery pi"
smaller are using microcontrollers that support [micropython](https://micropython.org/)

# Directory organization
## MQTT-home/Library
Code shared by both micropython and linux
## MQTT-home/linux
Linux IoT, typicaly RPI servers, linux projects live here
## MQTT-home/micropython
Currently ESP32-S2 projects. Anything else using micropython goes here.
### MQTT-home/micropython/library
libray of shared code specific to micropython devices

# sample IoT Network
## Requirements
All IP IoT devices must live in a private subnet. Wifi should be a mesh   
subnet must support both wired and WiFi IP devices  
Zigbee devices live in a PAN defined by zigbee2mqtt.    
## developmental system
TP-Link Deco x55 three node mesh WiFi router with 3 Gigabit ports each.  
This allows pretty much unlimited coverage for wired and well as wired devices.  
Simple end user setup.  
save the ssid and password in [network.json](https://github.com/jdodgen/MQTT-home/network.json)
to be shared as needed for install scripts.









