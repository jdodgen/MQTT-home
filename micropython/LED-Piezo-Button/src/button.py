# James Dodgen 2023, 2024
# MIT licence

# this was using interupts/IRQ and now is being polled
# the interupts messed with the async in mqtt_as.py
# this tends to be polled at the end of the main.py loop.
# Should come back and the the IRQ/mqtt_as problem fixed.
# the use of polling requires this processor to run and 
# not enter power saving sleep-and-wait mode
# waiting for an event. 

from universal_machine import machine, asyncio

class button:
	def __init__(self, pin, mqtt_client) # client is left here to ease fixing IRQ issue
		self.button_pin = machine.Pin(pin, machine.Pin.IN, machine.Pin.PULL_UP)
		 
	def test(self):
		value = self.button_pin.value()
		# print("button value[%s]" % (value,))
		return value
