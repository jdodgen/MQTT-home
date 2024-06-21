'''copyright 20123 James Dodgen  MIT licence
A few complexities:
system runs multiple proceeses
with communication through a queue as well as  a pipe
queue system handles both periodic flow values 
as well as commands to start the pump cycle.
'''
import multiprocessing
import queue
import time
import sys
import const
import web_server
import database
import mqtt_manager
from  run_pump_cycle import run_pump_cycle
import os
if os.name =="nt": # testing under Windows
	from flow_event_task_simulator import flow_event_task, pump_motor_relay, gpio_config
else:
	from flow_event_task import flow_event_task, pump_motor_relay, gpio_config
import signal
import sys

xprint = print # copy print
my_name = "main/trigger_loop"
def print(*args, **kwargs): # replace print
    return  # comment/uncomment to turn print on off
    # do whatever you want to do
    #xprint('statement before print')
    xprint(my_name, *args, **kwargs) # the copied real print

def trigger_loop(flow_commands_q, sender, shared_in, db_values):      
	global shared
	shared = shared_in
	db=database.database(db_values) 
	my_name="detecting_trigger"
	while True: # loop forever logging to shared and running pump cycle when requested 
		print("turn pump off before cycle") 
		pump_motor_relay(const.turn_pump_off, shared, sender) # always start with pump 
		print( "wait on queue")
		cmd, value = flow_commands_q.get() # block until it changes
		print( "got message cmd [%s] value [%s]" % (cmd, value,))                  
		if (cmd > const.flowing_cmds):
			shared[const.pump_cycle_reason]=cmd 
			run_pump_cycle(flow_commands_q, sender, shared, db)
		else: # Must be a flow status and pulse count
			shared[const.flow_switch_state] = cmd
			shared[const.pulses] = value   

if __name__ == '__main__':
	print("creating queues and mutiprocessing stuff")
	signal.signal(signal.SIGINT, lambda x, y: sys.exit(0))
	flow_commands_q = multiprocessing.Queue(10)
	reciever, sender =  multiprocessing.Pipe(duplex=False)
	db_values = multiprocessing.Array('i', const.db_values_size)
	db = database.database(db_values)
	db.load()
	shared = multiprocessing.Array('i', const.shared_size)
	shared[const.pump]=0
	shared[const.flow_switch_state]=0
	shared[const.pulses]=0
	shared[const.flow_switch_state] = const.unknown
	shared[const.flow_start_time] = int(time.time())
	shared[const.last_pump_time] = int(time.time())
	shared[const.pump_cycle_reason]=0
	shared[const.pump_stopped_reason]=0 
	
	gpio_config() # setup GPIO ports
	pump_motor_relay(const.turn_pump_off, shared, sender)
	flow = multiprocessing.Process(target=flow_event_task, args=(flow_commands_q, shared, db_values))    
	flow.start()
	detect = multiprocessing.Process(target=trigger_loop, args=(flow_commands_q, sender, shared, db_values))    
	detect.start()
	children = multiprocessing.Process(target=mqtt_manager.task, args=(shared, flow_commands_q, reciever))
	children.start()
	web = multiprocessing.Process(target=web_server.task, args=(flow_commands_q, shared, db_values))  
	web.start() 
	status_web = multiprocessing.Process(target=web_server.status_task, args=(shared,))  
	status_web.start()
	print("main: processes started now watchdog running")
	# watchdog 
	dead="Unknown"
	#time.sleep(10000)
	#web=None
	multiprocessing.connection.wait([flow.sentinel, web.sentinel, status_web.sentinel, detect.sentinel, children.sentinel])                     
	time.sleep(4)
	if (flow.is_alive()):
		flow.terminate()
		#flow.close()
	else:
		dead="flow"
	if (web.is_alive()):
		web.terminate()
		#web.close()
	else:
		dead="web"
	if (detect.is_alive()):
		detect.terminate() 
		#detect.close() 
	else:
		dead="detect"
	pump_motor_relay(const.turn_pump_off, shared, sender) # don't want to leave it on
	print("main: process [%s] died" % (dead,))  
	sys.exit("something died, reboot")
