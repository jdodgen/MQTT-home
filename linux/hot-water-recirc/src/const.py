# water heater controller constants author Jim Dodgen Copyright 2023-2024
# MIT license 
#
broker = "home-broker.local"
# commands to pump
turn_pump_off = 0
turn_pump_on = 1

# queue commands from flow sensor
not_flowing=0
flowing=1

flowing_cmds = 1  # used to see if we have non flowing commands
#anything greater than 1 is a command to run cycle

mqtt=2 # start cmd  MQTT
http=3 # from alertaway.com  home automation system

# reason for 
timed_out = 4
flow_stopped =5
unknown = 6

# cmd strings for printing
#          0              1         2        3           4               5            6
cmd = ["NOT FLOWING", "FLOWING", "MQTT", "http", "timed out", "flow stopped", "unknown"]

ColorRED = '\033[91m'

children_sleep_time = 5

hardware="rpi with wifi, zero-relay or opto relay boards"

version = "SW [%s] HW[%s]" % ("0.4", hardware)

flow_switch_GPIO = 23 # rpi pin 16 

# relays - we toggle all of the relay gpio lines so it does not matter which relay board you are using, add additional as needed
external_relay_GPIO = 24 # pin 18 the same on all rpi  (external relay board)
zero_relay_GPIO = 5 # pin 29 on the rpi this is the two relay hat,  trade name is "Zero Relay"
# others to be added later

relay_ports=[external_relay_GPIO, zero_relay_GPIO] # this is used by rpi_interface

db_name = "db.db"

# we share a simple array of numbers
# shared indexes
pump=0
flow_switch_state=1
pulses=2
flow_start_time=3
last_pump_time=4
pump_cycle_reason=5
pump_stopped_reason = 6
ltr_per_minute = 7
pulses_in_5_seconds = 8
last_pump_run_time=9
spare=10
shared_size=11

# shared array in database.py
db_values_size = 12 # change this when needed



# unit test area
if __name__ == '__main__':
    print(version)


