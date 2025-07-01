# MIT Licence copyright 2024 Jim Dodgen
# alerts like LED and Piezo

import machine
import time
import uasyncio as asyncio

# conditional print
xprint = print # copy print
def print(*args, **kwargs): # replace print
    #return # comment/uncomment to turn print on off
    # do whatever you want to do
    #xprint('statement before print')
    try:
        xprint("[alert_handler]", *args, **kwargs) # the copied real print
    except:
        raise ValueError("xprint problem ["+msg+"]")

class alert_handler:
    # this is a visual and optional sound notification

    def __init__(self, led_pin, piezo_pin):
        self.led = machine.Pin(led_pin,machine.Pin.OUT)
        self.led.off()
        if piezo_pin:
            self.piezo = machine.Pin(piezo_pin,machine.Pin.OUT)
            self.piezo.off()
        else:
            self.piezo = None

    def turn_on(self):
        print('turning led on(1) current', self.led.value())
        if (self.piezo and self.led.value() == 0):  # a little BEEP
            self.beep(count=1)
        self.led.value(1)

    def turn_off(self):
        print('turning led off(0) current', self.led.value())
        if (self.piezo and self.led.value() == 1):  # a little BEEP
            self.beep(count=1)
        self.led.value(0)

    def flash(self, count=0, duration=1, ontime=1):
        self.led.value(0)
        while True:
            self.led.value(1)
            time.sleep(ontime)
            self.led.value(0)
            count -= 1
            if (count < 1):
                break
            time.sleep(duration)

    async def async_flash(self, count=0, duration=1, ontime=1):
        self.led.value(0)
        for _ in range(count):
            self.led.value(1)
            await asyncio.sleep(ontime)
            self.led.value(0)
            await asyncio.sleep(duration)

    def beep(self, count=1):
        while True:
            self.piezo.on()
            time.sleep(0.2)
            self.piezo.off()
            count -= 1
            if (count < 1):
                break
            time.sleep(0.2)