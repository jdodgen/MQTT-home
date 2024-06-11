import os
import sys
try:
    if os.name == 'nt':
        sys.path.append("MQTT-library/library/") 
        sys.path.append("MQTT-micropython-library/") 
        import  dummy_machine as machine
        import asyncio
except:
    import uasyncio as asyncio   # version for micropython
    import machine

machine = machine
asyncio = asyncio


