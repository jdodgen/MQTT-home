import cfg
import machine
import uasyncio as asyncio

class chime:
    def __init__(self):
        self.play_all      = machine.Pin(cfg.play_all_pin,     machine.Pin.OUT)
        self.ding_dong     = machine.Pin(cfg.ding_dong_pin,    machine.Pin.OUT)
        self.ding_ding     = machine.Pin(cfg.ding_ding_pin,    machine.Pin.OUT)
        self.westminster  =  machine.Pin(cfg.westminster_pin,  machine.Pin.OUT)
        self.button = machine.Pin(cfg.button_pin, machine.Pin.IN, machine.Pin.PULL_UP)

        # turn it all off
        self.play_all.value(0)
        self.ding_dong.value(0)
        self.ding_ding.value(0)
        self.westminster.value(0)

    async def play_all(self):
        self.play_all.value(1)
        await asyncio.sleep(cfg.time_to_trigger)
        self.play_all.value(0)

    async def ding_dong(self):
        self.ding_dong.value(1)
        await asyncio.sleep(cfg.time_to_trigger)
        self.ding_dong.value(0)

    async def ding_ding(self):
        self.ding_ding.value(1)
        await asyncio.sleep(cfg.time_to_trigger)
        self.ding_ding.value(0)

    async def westminster(self):
        self.westminster.value(1)
        await asyncio.sleep(cfg.time_to_trigger)
        self.westminster.value(0)