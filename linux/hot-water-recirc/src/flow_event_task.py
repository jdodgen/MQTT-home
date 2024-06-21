import time
import RPi.GPIO as GPIO
import const
import database

xprint = print # copy print
my_name = "flow_event_task"
def print(*args, **kwargs): # replace print
    return  # comment/uncomment to turn print on/off
    # do whatever you want to do
    #xprint('statement before print')
    xprint(my_name, *args, **kwargs) # the copied real print
# 
def flow_event_task(flow_commands_q, shared, db_values): # this runs as a seperate task
	print("flow_event_task: starting")
	db = database.database(db_values)
	
	# old -- flow_commands_q.put(get_switch_value())    # get current state prime the pump
	pulses_per_sec = 0
	one_minute_timer_start =time.time()+5  # plus 5 sconds  
	while True: # run forever
		start = int(round(time.time() * 1000))
		timed_out_milliseconds = db.pulse_collection_milliseconds()
		timeout_time = start+timed_out_milliseconds
		time_left = timed_out_milliseconds
		print("flow_event_task time_left", time_left)
		pulse_count = 0
		got_count=0
		while True: # run while decreasing time out counting pulses     
			if time_left == 0:
				got_one = None 
			else:
				got_one = GPIO.wait_for_edge(const.flow_switch_GPIO, GPIO.RISING, timeout=time_left) # blocks until change or time out
			raw_now = time.time()
			if got_one is None:  # gpio timed out, 
				print("flow_event_task GPIO timed out")
				flow_commands_q.put(get_flow_state(db,pulse_count))
				got_count=1
			else:
				#print("flow_event_task got pulse", pulse_count)
				pulse_count += 1
				pulses_per_sec +=1
				now = int(round((raw_now * 1000)))                         
				if timeout_time < now: # looks like time has expired
					print("flow_event_task reached timed left")
					flow_commands_q.put(get_flow_state(db,pulse_count))
					got_count=1
				else:
					time_left = timeout_time - now
			if  one_minute_timer_start  < raw_now:
				record_flow_rate(db, pulses_per_sec, shared)
				pulses_per_sec = 0
				one_minute_timer_start = raw_now+5  # plus a second
			if got_count == 1:
					break
				

def record_flow_rate(db, current_pulses, shared):
	liters = int(round(current_pulses*20/db.pulses_per_ltr()))
	print("record_flow_rate current pulses", current_pulses)
	print("record_flow_rate milliliters per second", liters)
	if shared:
		shared[const.pulses_in_5_seconds]=current_pulses
		shared[const.ltr_per_minute]=liters
	return

def get_flow_state(db, pulses):
	if pulses <= db.min_pulses_to_turn_off():  
		print("get_flow_state not_flowing", pulses)
		cmd = const.not_flowing             
	else:
		print("get_flow_state flowing", pulses)
		cmd = const.flowing
	return [cmd,pulses] 	  

def pump_motor_relay(state, shared, sender):
	# 120/240V 10Amp relay, opticly isolated 
	print("pump_motor_relay", state, shared[const.pump])
	if shared[const.pump] != state:  #has this changed?
		shared[const.pump] = state
		try:
			print("pipe: attempting for faster MQTT notification")
			sender.send(b'do it')
			print("pipe: WORKED")
		except:
			print("pipe: FAILED")
			pass
	control_pump(state)

# GPIO pin high/True for pump ON 
def control_pump(state):
	print("control_pump state[%s]" % (state,))
	if (state == const.turn_pump_on):
		for gpio in const.relay_ports:
			GPIO.output(gpio, True)
	else:   # turn_pump_off
		for gpio in const.relay_ports:
			GPIO.output(gpio, False)
		
def gpio_config():
	GPIO.setmode(GPIO.BCM) # broadcom numbers
	GPIO.setup(const.flow_switch_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)
	for gpio in const.relay_ports:
		GPIO.setup(gpio, GPIO.OUT)

# unit test area TU prefix
if __name__ == "__main__":
	print("motor_relay_GPIO[%s] flow_switch_GPIO[%s]" % (const.relay_ports, const.flow_switch_GPIO, ))
	gpio_config()

	'''
	# test to see if relay configured/working
	while True:
		print("TU turning pump ON")
		control_pump(const.pump_on)   # 1
		time.sleep(3)
		print("TU turning pump OFF")
		control_pump(const.pump_off)  # 0
		time.sleep(3)
	'''
	
	# test flow_event_task should send stream of messages
	import multiprocessing
	db_values = multiprocessing.Array('i', const.db_values_size)
	db = database.database(db_values)
	db.load()
	flow_commands_q = multiprocessing.Queue(10)
	flow = multiprocessing.Process(target=flow_event_task, args=(flow_commands_q, None, db_values))    
	flow.start()
	while True:
		cmd, value = flow_commands_q.get()
		xprint ("cmd[%s] value[%s]" % (cmd, value,))