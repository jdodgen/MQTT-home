def detecting_flow_task(flow_commands_q, sender, shared_in, db_values):      
	global shared
	shared = shared_in
	#global db
	db=database.database(db_values) 
	#shared=shared_in 
	my_name="detecting_flow_task"
	while True: # loop forever  
		# this is a "turn on hot water" loop # we need a transition 
		# from "not_flowing" to "flowing" to start this process 
		print_current_state(my_name,"turn pump off just for sure") 
		pump_motor_relay(const.pump_off, shared, sender) # always start with pump 
		print_current_state(my_name, "looking for the start flow") 
		if (shared[const.flow_switch_state] != const.not_flowing): # we have to start with it not_flowing
			print_current_state(my_name, "reset while flowing, so we wait") 
			while True:
				print_current_state(my_name, "wait on queue")
				deq = flow_commands_q.get() # True) # block until it changes
				print_current_state(my_name, "got message [%s]" % (deq[0],))               
				shared[const.flow_switch_state] = deq[0]
				shared[const.pulses] = deq[1]               
				
				if (shared[const.flow_switch_state] == const.external):
					run_pump_cycle(flow_commands_q, sender, shared, db, const.external)
				elif (shared[const.flow_switch_state] == const.not_flowing):
					print_current_state(my_name, "it is now not_flowing") 
				break                                               
		
		# if NOT an external then we continue normal
		elif (shared[const.flow_switch_state] != const.external):                             
			try:
				[shared[const.flow_switch_state], shared[const.pulses]] = flow_commands_q.get() #, db.max_pump_on_seconds())
			except queue.Empty:         
				print_current_state(my_name,"queue timed out db.max_pump_on_seconds")
				# so just loop, no big deal                     
			else:
				# got somthing 
				if (shared[const.flow_switch_state] == const.external):
						run_pump_cycle(flow_commands_q, sender, shared, db, const.external)             
				elif (shared[const.flow_switch_state] == const.not_flowing): # nothing flowing yet, ignore
					print_current_state(my_name,"nothing flowing yet")
					# valve is off so ignore
				else:   
					print_current_state(my_name,"> flow_detected_check_for_trigger")
					flow_detected_check_for_trigger(flow_commands_q, sender, shared, db)
		else: # we should nt get here, for testing fail. 
			print("Got a bad state", shared[const.flow_switch_state])
			sys.exit("Got a bad state")
 
			
# water now flowing, shared[const.flow_switch_state] == True
def flow_detected_check_for_trigger(flow_commands_q, sender, shared, db):    
	my_name="2 flow_detected_check_for_trigger"
	#global shared 
	#global db     
	shared[const.flow_start_time]=int(time.time())
	#is_flowing = 1
	print_current_state(my_name,"timer started")    
	while True: # now looking for a False saying flow is off                       
		[shared[const.flow_switch_state], shared[const.pulses]] = flow_commands_q.get() # every pulse_collection time
		print_current_state(my_name,"queue returned")
		if (shared[const.flow_switch_state] == const.external):
			run_pump_cycle(flow_commands_q, sender, shared, db, const.external)
			break
		# we need to collect shared[const.flow_switch_state] == flowing for trigger_on_to_off_milliseconds_min 
	
		milliseconds = int((time.time()-shared[const.flow_start_time])*1000)
		if  (shared[const.flow_switch_state] == const.flowing):  # it is still on           
			if (milliseconds > db.trigger_on_to_off_milliseconds_max()): # been on a to long
				return # no trigger
		else: # NOT flowing             
			# was it shut off between the min and max 
			if (milliseconds > db.trigger_on_to_off_milliseconds_min() and milliseconds <= db.trigger_on_to_off_milliseconds_max()):
				run_pump_cycle(flow_commands_q, sender, shared, db, const.on_off_sequence)
			break            