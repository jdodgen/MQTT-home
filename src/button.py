# James Dodgen 2023, 2024
# MIT licence

# recent odd changes were because mqtt_as and async broke
# my queue. so now just a sort of shared memory between the intwerupt routine
# and the main process  see remote_config.py

from universal_machine import machine, asyncio

class button:
	def __init__(self, pin): #, mqtt_client)
		self.button_pin = machine.Pin(pin, machine.Pin.IN, machine.Pin.PULL_UP)
		 
	def test(self):
		value = self.button_pin.value()
		# print("button value[%s]" % (value,))
		return value