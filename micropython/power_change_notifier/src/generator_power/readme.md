# generator power monitor
## this is the part plugged into an outlet that is on when the generator/secondary power is on

Flow:
 - Boot
 - connect to wifi
 - connect to MQTT Broker
 - MQTT subscribe to "utility_power_alive"  From [utility](../../utility_power)
 - MQTT publish secondary_powered_alive in a loop.
 - wait a few seconds for power_alive publish.
 - if utility_power_alive arrived?  quit
 - no utility_power_alive mesages arrived 
 - turn on LED
 - wait for power_alive publish
 - when power_alive arrives
 - turn off LED
 - now idle until network problems. then flashes the error
 - 
### notes
Flashing LED Codes:   
   - 2 ssid not found
   - 3 wifi password failed
   - 4 MQTT Broker DNS lookup failed
   - 5 unable to connect to the MQTT Broker
