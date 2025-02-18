# utility outlet monitor
# powered by utility power not powered by the backup generator or other secondary power source.

flow:
 - booting
 - connect wifi
 - connect to MQTT Broker
 - flash a LED a short time
 - publish power_alive messages forever
