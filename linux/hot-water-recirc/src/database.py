import sqlite3
import const

#shared memory -- db_values array -- indexes
trigger_on_to_off_milliseconds_min  = 0
trigger_on_to_off_milliseconds_max  = 1
cycles_to_run_after_pump_on_before_checking_flow =2
max_pump_on_seconds            = 3
last_seconds_pump_off_no_flow  = 4
pulse_collection_milliseconds  = 5
pulses_per_ltr	                =6
min_pulses_to_turn_off  =7
max_pulses_to_turn_off  =8
do_we_send_to_AlertAway        = 9
minimum_number_of_children = 10


class database:
	def __init__(self, db_values_in):
		self.db_values = db_values_in
		con = sqlite3.connect(const.db_name)
		cur = con.cursor()
		try:  # see if  db exists
			cur.execute("select max_pump_on_seconds from settings")
		except:
			self.initialize()
		cur.close()
		con.close()
				
	def trigger_on_to_off_milliseconds_min(self): # must be between min and max to trigger pump cycle        
		return self.db_values[trigger_on_to_off_milliseconds_min]
	
	def trigger_on_to_off_milliseconds_max(self): # must be between min and max to trigger pump cycle
		return self.db_values[trigger_on_to_off_milliseconds_max]
	
	def cycles_to_run_after_pump_on_before_checking_flow(self):
		return self.db_values[cycles_to_run_after_pump_on_before_checking_flow]
	
	def max_pump_on_seconds(self):
		return self.db_values[max_pump_on_seconds]
	
	def last_seconds_pump_off_no_flow(self, seconds):
		self.db_values[last_seconds_pump_off_no_flow] = seconds
		print("last_seconds_pump_off_no_flow", seconds)
	
	def pulse_collection_milliseconds(self): # how long to collect a sample
		return self.db_values[pulse_collection_milliseconds]
		
	def pulses_per_ltr(self):
		return self.db_values[pulses_per_ltr]
	
	def min_pulses_to_turn_off(self):
		return self.db_values[min_pulses_to_turn_off]
		
	def max_pulses_to_turn_off(self):
		return self.db_values[max_pulses_to_turn_off]
	
	def do_we_send_to_AlertAway(self):
		return self.db_values[do_we_send_to_AlertAway]

	def minimum_number_of_children(self):
		return self.db_values[minimum_number_of_children]

	# set values
	def set_trigger_on_to_off_milliseconds_min(self,i): 
		print("set_trigger_on_to_off_milliseconds_min [%s]" % (i,))
		self.db_values[trigger_on_to_off_milliseconds_min] = int(i)
	
	def set_trigger_on_to_off_milliseconds_max(self,i):
		self.db_values[trigger_on_to_off_milliseconds_max] = int(i)
	
	def set_cycles_to_run_after_pump_on_before_checking_flow(self,i):
		self.db_values[cycles_to_run_after_pump_on_before_checking_flow] = int(i)
	
	def set_max_pump_on_seconds(self,i):
		self.db_values[max_pump_on_seconds] = int(i)
	
	def set_pulse_collection_milliseconds(self,i): # how long to collect a sample
		self.db_values[pulse_collection_milliseconds] = int(i)
	
	def set_pulses_per_ltr(self,i): 
		self.db_values[pulses_per_ltr] = int(i)
		
	def set_min_pulses_to_turn_off(self,i):
		self.db_values[min_pulses_to_turn_off] = int(i)
		
	def set_max_pulses_to_turn_off(self,i):
		self.db_values[max_pulses_to_turn_off] = int(i)
	
	def set_do_we_send_to_AlertAway(self,i):
		self.db_values[do_we_send_to_AlertAway] = int(i)

	def set_minimum_number_of_children(self,i):
		self.db_values[minimum_number_of_children] = int(i)    
	
	def load(self):
		con = sqlite3.connect(const.db_name)
		cur = con.cursor()
		cur.execute("""
		select
			trigger_on_to_off_milliseconds_min, 
			trigger_on_to_off_milliseconds_max, 
			cycles_to_run_after_pump_on_before_checking_flow,
			max_pump_on_seconds,
			last_seconds_pump_off_no_flow,
			pulse_collection_milliseconds,
			pulses_per_ltr,
			min_pulses_to_turn_off,
			max_pulses_to_turn_off,
			do_we_send_to_AlertAway,
			minimum_number_of_children 
		from settings;
		""")
		settings = cur.fetchone()
		ndx=0
		# load shared db array Note: QUERY ORDER must be THE SAME AS db_values ARRAY
		for s in settings:
			print(s, ndx)
			self.db_values[ndx] = s
			ndx += 1        
		cur.close()
		con.close()
   
	def update_shared_data(self):
		con = sqlite3.connect(const.db_name)
		cur = con.cursor()
		cur.execute("""
		update settings 
			set trigger_on_to_off_milliseconds_min = ?, 
			trigger_on_to_off_milliseconds_max = ?, 
			cycles_to_run_after_pump_on_before_checking_flow = ?,
			max_pump_on_seconds = ?,
			last_seconds_pump_off_no_flow = ?,
			pulse_collection_milliseconds = ?,
			pulses_per_ltr = ?,            
			min_pulses_to_turn_off = ?,
			do_we_send_to_AlertAway = ?,
			minimum_number_of_children = ?
			""", 
			(self.db_values[trigger_on_to_off_milliseconds_min], 
			self.db_values[trigger_on_to_off_milliseconds_max], 
			self.db_values[cycles_to_run_after_pump_on_before_checking_flow],
			self.db_values[max_pump_on_seconds],
			self.db_values[last_seconds_pump_off_no_flow],           
			self.db_values[pulse_collection_milliseconds],
			self.db_values[pulses_per_ltr],
			self.db_values[min_pulses_to_turn_off],
			self.db_values[do_we_send_to_AlertAway],
			self.db_values[minimum_number_of_children]))
		cur.close()
		con.commit()
		con.close()
			   
	def initialize(self):
		con = sqlite3.connect(const.db_name)
		cur = con.cursor()
		cur.executescript("""    
		drop table if exists settings;
		create table settings 
		(
			trigger_on_to_off_milliseconds_min, --  must be between min and max to trigger pump cycle
			trigger_on_to_off_milliseconds_max, --  must be between min and max to trigger pump cycle
			cycles_to_run_after_pump_on_before_checking_flow,
			max_pump_on_seconds,
			last_seconds_pump_off_no_flow,
			pulse_collection_milliseconds , --  how long to collect a sample in milliseconds
			pulses_per_ltr,
			min_pulses_to_turn_off,  -- only run pump > min and < max
			max_pulses_to_turn_off,
			do_we_send_to_AlertAway, -- future feature to notify AlertAway pump on/off
			minimum_number_of_children
		);

		-- default settings  done this way to make setting defaults easier --
		insert into settings (trigger_on_to_off_milliseconds_min) values      (3000);                 
		update settings set trigger_on_to_off_milliseconds_max               = 5000;          
		update settings set cycles_to_run_after_pump_on_before_checking_flow = 2;          
		update settings set max_pump_on_seconds                             = 180;          
		update settings set pulse_collection_milliseconds                   = 1000;          
		update settings set min_pulses_to_turn_off                  = 17; 
		update settings set max_pulses_to_turn_off                  = 50; 
		update settings set pulses_per_ltr                                   = 477;
		update settings set last_seconds_pump_off_no_flow                    = 0;          
		update settings set do_we_send_to_AlertAway                          = 0;
		update settings set minimum_number_of_children                       = 1;          

		drop table if exists log;
		create table log
		(
			time_started integer primary key,
			duration,
			start_action,
			stop_reason
		);

		""")
		cur.close()
		con.commit()
		con.close()

# for testing only
if __name__ == "__main__":
	import multiprocessing
	db_values = multiprocessing.Array('i', const.db_values_size)
	db=database(db_values)
	db.initialize()
	db.load()
	db.update_shared_data()
	print(db.pulse_collection_milliseconds())

