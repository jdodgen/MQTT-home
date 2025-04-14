# A cluster of smart power sensors
### overview
-  all sensors "watch" all the "other" sensors.
-  emails sent when sensors are lost and a LED turned on
- typical usecase is watching: generators, utility, solar, and battery, for outages
- All sensors are independent and equal.

### Flow:
 - Boot
 - connect to wifi
 - connect to MQTT Broker
 - MQTT subscribe to the other sensors
 - wait TBD seconds for subscribed messages.
 - runing in a TBD second loop
     - publish our status
     - count times NO message (sensor off)  
     - after a TBD count send email
     - turn on and off LED if any "other sensors are off)
- bunch of fault tollarance stuff
 - 
### Diagnostic LED Codes:  
- 1 booting up
- 2 wifi ssid not found
- 3 wifi password failed
- 4 MQTT Broker DNS lookup failed
- 5 unable to connect to the MQTT Broker
     

Each sensor will send an email when another sensor is down
