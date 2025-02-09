# power change notifier
two esp32-s2 microcontrolers that talk via MQTT and cause emails/sms messages to be sent   
this includes micropython code, pictures of the hand wired board as well as scad and stl files to make the enclosure.

The system consists of:
 - Utility monitor, publishes MQTT status that utility is supplying power
 - Generator monitor, subscribes to the above MQTT and sends emails when the state changes.
 - MQTT broker, if not using home-broker then a small cheap linux with [mosquitto](https://mosquitto.org/)

/etc/mosquitto/mosquitto.conf needs to contain
```
allow_anonymous true
listener 1883
log_dest none"
```
