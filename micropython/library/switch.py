# copyright James Dodgen 2025
# MIT license

# typically switch.test() is called in the main.py asyncio
# loop hopefully with something to do or a sleep(0.3).
#

from universal_machine import machine
class switch:
    def __init__(self, pin, mqtt_client):
        self.mqtt_client = mqtt_client # client is here when IRQ fixed
        self.button_pin = machine.Pin(pin, machine.Pin.IN, machine.Pin.PULL_UP)

    def test(self):
        value = self.button_pin.value()
        # print("switch value[%s]" % (value,))
        return value

# switch(1,2)
