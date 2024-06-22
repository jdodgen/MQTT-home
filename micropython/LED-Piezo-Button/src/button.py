# James Dodgen 2023, 2024
# MIT licence

# this was using interupts/IRQ and now is being polled
# the interupts messed with the async in mqtt_as.py
# 
# typicaly button.test() is called in the main.py 
# loop hopefully with somthing to do or a sleep(0.3).
#
# shpuld redo when the IRQ/mqtt_as problem fixed.
# the use of polling requires this processor to run and 
# not enter power saving sleep-and-wait mode
# waiting for an event. 

from universal_machine import machine
class button:
	def __init__(self, pin, mqtt_client):
		self.mqtt_client = mqtt_client # client is here when IRQ fixed
		self.button_pin = machine.Pin(pin, machine.Pin.IN, machine.Pin.PULL_UP)
		 
	def test(self):
		value = self.button_pin.value()
		# print("button value[%s]" % (value,))
		return value

# button(1,2)
