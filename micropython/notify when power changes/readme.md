# power change notifier
two esp32-s2 microcontrolers that talk via MQTT and cause emails/sms messages to be sent   
this includes micropython code, pictures of the hand wired board as well as scad and stl files to make the enclosure.

The system consists of:
 - utility monitor, publishes MQTT status that utilitynpower is up.
 - generator monitor, subscribes to the above MQTT and sends emails when the state changes.
 - MQTT broker, if not using home-broker then a small cheap linux with [mosquitto](https://mosquitto.org/)

