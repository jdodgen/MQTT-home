# MIT Licence 2024 Jim Dodgen
# 
from universal_machine import machine, asyncio
import time

# esp32-s2 , # mapped to  "WeMos D1 Mini" pins
open_relay_pin  = 35  # D1
close_relay_pin = 33  # D2

# feed back
full_open_pin   = 16   # D3
full_closed_pin = 18   # D4

# conditional print
xprint = print # copy print
def print(*args, **kwargs): # replace print
    #return # comment/uncomment to turn print on off
    # do whatever you want to do
    #xprint('statement before print')
    xprint("[water_valve]", *args, **kwargs) # the copied real print    

class water_valve:
    def __init__(self, client, on_off, max_motor_on_time, problem):
        self.client = client
        self.on_off = on_off
        self.problem = problem
        self.max_motor_on_time = max_motor_on_time
        print("test states [%s][%s]" % (self.on_off.payload_off(), self.on_off.payload_on(),))
        # 1 cause 3.3v and closes relay
        self.state = "unknown"
        self.open_relay = machine.Pin(open_relay_pin,machine.Pin.OUT)
        self.close_relay = machine.Pin(close_relay_pin,machine.Pin.OUT)
        # closure pulls to ground
        self.full_closed_sensor = machine.Pin(full_closed_pin, machine.Pin.IN, machine.Pin.PULL_UP)
        self.full_open_sensor = machine.Pin(full_open_pin, machine.Pin.IN, machine.Pin.PULL_UP)
        if self.full_closed_sensor.value() or self.full_open_sensor.value():  # open or shut so leave it that way #   value = self.button_pin.value() 
            # turn everything off, just to be safe
            self.close_relay.value(0) # make sure  relay is off
            self.open_relay.value(0) # make sure relay is  off
        else:  # unknown if open or closed. best to just close it
            self.close()

    async def open(self):
        print('open: current port values open_relay {} close_relay {} limit_open {} limit_closed {}'.format( 
              self.open_relay.value(), self.close_relay.value(), self.full_open_sensor.value(), self.full_closed_sensor.value()))
        await self.run_valve_motor("opening", self.open_relay, self.full_open_sensor, self.close_relay)
        
    async def close(self):
        print('close: current port values open_relay {} close_relay {} limit_open {} limit_closed {}'.format( 
              self.open_relay.value(), self.close_relay.value(), self.full_open_sensor.value(), self.full_closed_sensor.value()))
        await self.run_valve_motor("closing", self.close_relay, self.full_closed_sensor, self.open_relay)
        
    # motor direction of rotation driven by polarity. two relays flip flop the "+"" and "-"" 
    async def run_valve_motor(self, direction, wanted, sensor, not_wanted):
        not_wanted.value(0) # make sure open relay is off GROUND relay on NC
        # just spinning until done, should have a timeout to detect broken valve/sensor
        runtime = 0
        while sensor.value() :  # not 0  yet, pulled down when motor run cycle complete
            wanted.value(1) # turn/leave relay on
            print("run_motor_valve: %s relay value [%s]" % (direction, sensor.value(),))
            time.sleep(1)
            runtime += 1
            if runtime > self.max_motor_on_time:
                await self.client.publish(self.problem.topic(), "timedout: [%s] %s seconds" % (direction, self.max_motor_on_time,)) 
                break
        wanted.value(0) # turn relay off

    def status(self, x):
        print('{} current  values open_relay {} close_relay {} limit_open {} limit_closed {}'.format( 
              x, self.open_relay.value(), self.close_relay.value(), self.full_open_sensor.value(), self.full_closed_sensor.value()))

    async def current_state(self):
        print("current_state states [%s][%s]sensor[%s]" % (self.on_off.payload_off(), self.on_off.payload_on(),self.full_open_sensor.value(),))
        if self.full_closed_sensor.value()  == 0: # 0 pulled to ground pay closed or water is "off"
            return self.on_off.payload_off() # "closed water is off"
        if self.full_open_sensor.value()  == 0: #  0 pulled to ground water os flowing or "on"
            return self.on_off.payload_on() 
        else:
            return self.on_off.payload_unknown() # "partial?"

#wv = water_valve(None)
# wv.open()