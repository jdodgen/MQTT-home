# alerts like LED and Piezo

from universal_machine import machine, asyncio
import time

class alert_handler:
    # this is a visual and sound notification
    
    def __init__(self, led_pin, piezo_pin):
        self.led =   machine.Pin(led_pin, machine.Pin.OUT)
        self.led.value(0)
        self.piezo = machine.Pin(piezo_pin, machine.Pin.OUT)
        self.piezo.value(0)

    def turn_on(self):
        print('turning led on(1) current', self.led.value())
        if (self.led.value() == 0):  # a little BEEP
            self.beep(count=1)
        self.led.value(1)
        
    def turn_off(self):
        print('turning led off(0) current', self.led.value())
        if (self.led.value() == 1):  # a little BEEP
            self.beep(count=1)
        self.led.value(0)

    def flash(self, count=0):
        self.led.value(0)
        while True:
            self.led.value(1)
            time.sleep(1)
            self.led.value(0)
            count -= 1
            if (count < 1):
                break
            time.sleep(1)

    def beep(self, count=1):
        while True:
            self.piezo.value(1)
            time.sleep(0.2)
            self.piezo.value(0)
            count -= 1
            if (count < 1):
                break
            time.sleep(0.2)