import os
import sys
try:
    if os.name == 'nt':
        sys.path.append("MQTT-library/library/") 
        sys.path.append("MQTT-micropython-library/") 
        import  dummy_mqtt_as as mqtt_as
        import asyncio
except:
    import uasyncio as asyncio   # version for micropython
    import mqtt_as

config = mqtt_as.config
MQTTClient = mqtt_as.MQTTClient
asyncio = asyncio


