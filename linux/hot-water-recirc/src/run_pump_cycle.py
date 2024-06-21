
import const
import time
import os
if os.name =="nt": # testing under Windows
	from flow_event_task_simulator import pump_motor_relay
else:
	from flow_event_task import pump_motor_relay


my_name="run_pump_cycle"
xprint = print # copy print
def print(*args, **kwargs): # replace print
    #return  uncomment to turn print off
    # do whatever you want to do
    #xprint('statement before print')
    xprint(my_name, *args, **kwargs) # the copied real print

def run_pump_cycle(flow_commands_q, sender, shared, db):
	pump_start_time = time.time()
	# already flowing so exit
	if (shared[const.flow_switch_state] == const.flowing): 
		return   
	pump_motor_relay(const.turn_pump_on, shared, sender)
	shared[const.last_pump_time]=int(pump_start_time)
	shared[const.pump_stopped_reason]=0
	print("now we pump max_pump_on_seconds or get a flow pump_off after flowing") 
	# give the pump some time to start, so eat some cycles
	cycles=db.cycles_to_run_after_pump_on_before_checking_flow()
	while cycles > 0: # run at start to give flow time to catch up
		cmd, value = flow_commands_q.get()
		if cmd > const.flowing_cmds:
			continue
		shared[const.flow_switch_state] = cmd
		shared[const.pulses]  = value
		print("cycles_to_run_after_pump_on_before_checking_flow")
		cycles-=1
	while True: # now we wait for a timeout or a flow pump_off       
		cmd, value = flow_commands_q.get()
		if cmd > const.flowing_cmds:
			continue
		shared[const.flow_switch_state] = cmd
		shared[const.pulses]  = value
		print("wait for timeout loop: cmd[%s] pulses[%s]" % (cmd, value,))
		if (shared[const.flow_switch_state] == const.flowing): # it is flowing 
			print("flowing: pump_start_time[%s] max_pump_on_seconds[%s]" % (pump_start_time, db.max_pump_on_seconds(),))
			if (pump_start_time+db.max_pump_on_seconds() > time.time()):                
				print("flowing and not max_pump_on_seconds")
				continue
			else:  # timed out
				print("timed out, so turn pump_off pump and we are done")
				pump_motor_relay(const.turn_pump_off, shared, sender)
				shared[const.pump_stopped_reason]=const.timed_out
				break
		else: # not flowing         
			# Ok the Grundfos valve(s) have now closed , so we are done
			db.last_seconds_pump_off_no_flow(round(time.time() - pump_start_time))
			print("not_flowing, so turn pump_off pump and we are done")
			pump_motor_relay(const.turn_pump_off, shared, sender)
			shared[const.pump_stopped_reason]=const.flow_stopped
			break
	pump_stop_time = time.time()
	shared[const.last_pump_run_time]=int(pump_stop_time) - int(pump_start_time)
