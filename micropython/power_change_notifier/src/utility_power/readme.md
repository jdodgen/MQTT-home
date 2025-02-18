# utility outlet monitor
# powered by utility power not powered by the backup generator or other secondary power source.

flow:
 - booting
 - connect wifi
 - connect to MQTT Broker
 - flash a LED a short time
 - publish utility_power_alive messages forever
 - subscribed to by one or more [generator_power](../.../generator_power) devices or ?

### notes
Flashing LED Codes:   
   - 2 ssid not found
   - 3 wifi password failed
   - 4 MQTT Broker DNS lookup failed
   - 5 unable to connect to the MQTT Broker
