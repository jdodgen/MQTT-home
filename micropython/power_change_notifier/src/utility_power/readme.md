# old version soon to be deleted
## utility outlet monitor
### Powered by utility power and not powered by the generator/secondary power.

flow:
 - booting
 - connect wifi
 - connect to MQTT Broker
 - flash a LED a short time
 - publish utility_power_alive messages forever
 - subscribed to by one or more [generator_power](../.../generator_power) devices or ?

### notes
Flashing LED Codes:   
   - 2 wifi ssid not found
   - 3 wifi password failed
   - 4 MQTT Broker DNS lookup failed
   - 5 unable to connect to the MQTT Broker
