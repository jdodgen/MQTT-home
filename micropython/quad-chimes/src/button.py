# James Dodgen 2023, 2024
# MIT license

# recent odd changes were because mqtt_as or uasync broke
# my use of a queue. so now just a sort of shared memory between the interrupt routine
# and the main process  see remote_config.py
import machine
import uasyncio as asyncio  # micropython version 

class button:
	def __init__(self, pin): #, mqtt_client)
		self.button_pin = machine.Pin(pin, machine.Pin.IN, machine.Pin.PULL_UP)
		 
	def test(self):
		value = self.button_pin.value()
		# print("button value[%s]" % (value,))
		return value