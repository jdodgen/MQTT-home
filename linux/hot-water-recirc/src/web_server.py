
from flask import Flask, Response, render_template_string, stream_with_context, request
from gevent.pywsgi import WSGIServer
import os
import socket
import json
import time
import const
import database
import index_html
import status_html
# import threading
#import broadcast_to_children
import os 

xprint = print # copy print
my_name="web_server"
def print(*args, **kwargs): # replace print
    #return  uncomment to turn print off
    # do whatever you want to do
    #xprint('statement before print')
    xprint(my_name, *args, **kwargs) # the copied real print

def render_screen(db):
	print("render_screen: called")
	testIP = "8.8.8.8"
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.connect((testIP, 0))
	IPAddr = s.getsockname()[0]
	print(IPAddr)
	return render_template_string(index_html.html,
		trigger_min =      db.trigger_on_to_off_milliseconds_min(),
		trigger_max =      db.trigger_on_to_off_milliseconds_max(),
		cycles_to_run =    db.cycles_to_run_after_pump_on_before_checking_flow(),
		max_pump =         db.max_pump_on_seconds(),
		pulse_collection = db.pulse_collection_milliseconds(),
		min_pulses =       db.min_pulses_to_turn_off(),
		max_pulses =       db.max_pulses_to_turn_off(),
		aa =               db.do_we_send_to_AlertAway(),
		minimum_number_of_children = db.minimum_number_of_children(),
		pulses_per_ltr = db.pulses_per_ltr(),
		ipaddr = IPAddr,
		version = const.version)
		
class task():
	def __init__(self,flow_commands_q, shared_in, db_values_in):
		#from gevent import monkey; monkey.patch_all()
		self.shared =shared_in
		self.q =flow_commands_q
		self.db_values = db_values_in
		self.db=database.database(self.db_values)
		app = Flask(__name__)
		app.add_url_rule('/', 			view_func=self.render_index, methods =["GET", "POST"])
		app.add_url_rule('/whoareyou', 	view_func=self.whoareyou, methods =["GET", "POST"])
		app.add_url_rule('/extern', 	view_func=self.extern, methods =["GET", "POST"])
		app.add_url_rule('/action', 	view_func=self.render_action, methods =["GET", "POST"])
		app.add_url_rule('/runit', 		view_func=self.runit, methods =["GET", "POST"])
		app.add_url_rule('/testing', 	view_func=self.testing, methods =["GET", "POST"])
		app.add_url_rule('/defaults',	view_func=self.defaults, methods =["GET", "POST"])
		app.add_url_rule('/reboot', 	view_func=self.reboot, methods =["GET", "POST"])
		app.add_url_rule('/listen', 	view_func=self.listen, methods =["GET", "POST"])
		app.add_url_rule('/status', 	view_func=self.status, methods =["GET", "POST"])
	#btc=broadcast_to_children.broadcast_to_children(db, 9000,const.version)
		print("Starting web server")
	# app.run(port=80, debug=True)
		http_server = WSGIServer(("0.0.0.0", 80), app)
		http_server.serve_forever()
		print("should not get here")
	
	def render_index(self):
		print("render_index: sending index.html")
		return render_screen(self.db)

	def whoareyou(self):
		myhost = os.uname()[1]
		print("host name ", myhost)
		return "iam/"+myhost

	def extern(self):
		print("http extern")  
		self.q.put([const.http,0])
		return "Ok"
				
	def render_action(self):
		print("render_action: [%s] form [%s]" % (request.method,request.form,))
		db=database.database(self.db_values)
		if request.method == "POST":
			print("in post")
			try:      
				self.db.set_cycles_to_run_after_pump_on_before_checking_flow (request.form["cycles_to_run"])
				self.db.set_max_pump_on_seconds                (request.form["max_pump"])
				self.db.set_pulses_per_ltr                       (request.form["pulses_per_ltr"])
				self.db.set_pulse_collection_milliseconds      (request.form["pulse_collection"])
				self.db.set_min_pulses_to_turn_off     (request.form["min_pulses"])
				self.db.set_max_pulses_to_turn_off     (request.form["max_pulses"])
				self.db.set_minimum_number_of_children     (request.form["minimum_number_of_children"])
				#self.db.set_do_we_send_to_AlertAway            (request.form["aa"])
				self.db.update_shared_data()
				print("in post: min",self.db.trigger_on_to_off_milliseconds_min()) 
			except:
				print("render_action: db update failed")
		return render_screen(self.db)  
	
	def status(self):
		print("http status")  
		return render_template_string(status_html.html)
	
	def runit(self):
		self.q.put([const.http,0])
		print("http getting run")  
		return render_screen(self.db)

	def testing(self):
		self.btc.send("testing")
		print("http testing children")  
		return render_screen(self.db)
	
	def defaults(self):
		self.db.initialize()
		self.db.load()
		print("initialized")
		return render_screen(self.db)
	
	def reboot(self):
		print("rebooting")	
		os._exit(-1)

	def listen(self):
		print("listen called")

		def respond_to_client():
			while True:
				if (self.shared[const.pump] == const.turn_pump_on):
					motor = "PUMP ON"
					color="#40E0D0"
				elif (self.shared[const.pump] == const.turn_pump_off):
					motor = "PUMP OFF"
					color="gray"
				else:
					motor = "Unknown" 
						
				flow = const.cmd[self.shared[const.flow_switch_state]]
				
				#print(self.shared[const.pulses])
				#status = f" {motor} -- [{flow}["+str(self.shared[const.pulses])+"]]"
				t=time.strftime("%H:%M:%S", time.localtime())
				last=time.strftime("%H:%M:%S", time.localtime(self.shared[const.last_pump_time]))
				status = (f"now: {t}\n"+
					f"last_pump_run_time: {last}\n"+
					f"pump_cycle_reason[{const.cmd[self.shared[const.pump_cycle_reason]]}]\n"+
					f"pump_stopped_reason[{const.cmd[self.shared[const.pump_stopped_reason]]}]\n" +
					f"CURRENT: [{motor}:{flow}]\n"+
					f"pulses in last pulse_collection [{self.shared[const.pulses]}]\n"+
					f"pulses in 5 seconds[{self.shared[const.pulses_in_5_seconds]}]\n"+
					f"flow L/m [{float(self.shared[const.ltr_per_minute])}]")
					
				_data = json.dumps({"color":color, "status":status})
				yield f"id: 1\ndata: {_data}\nevent: online\n\n"
				#yield f"id: 1\ndata: {status}\nevent: online\n\n"           
				time.sleep(1)
		return Response(respond_to_client(), mimetype='text/event-stream')

class status_task():
	def __init__(self, shared_in):
		#from gevent import monkey; monkey.patch_all()
		self.shared =shared_in
		app = Flask(__name__)
		app.add_url_rule('/listen', 	view_func=self.listen, methods =["GET", "POST"])
		app.add_url_rule('/', view_func=self.status, methods =["GET", "POST"])
		print("Starting web status server")
	# app.run(port=80, debug=True)
		http_server = WSGIServer(("0.0.0.0", 9000), app)
		http_server.serve_forever()
		print("should not get here")

	def status(self):
		print("http status")  
		return render_template_string(status_html.html)
	
	def listen(self):
		print("listen called")
		def respond_to_client():
			while True:
				if (self.shared[const.pump] == const.turn_pump_on):
					motor = "PUMP ON"
					color="#40E0D0"
				elif (self.shared[const.pump] == const.turn_pump_off):
					motor = "PUMP OFF"
					color="gray"
				else:
					motor = "Unknown" 
						
				flow = const.cmd[self.shared[const.flow_switch_state]]
				
				#print(self.shared[const.pulses])
				#status = f" {motor} -- [{flow}["+str(self.shared[const.pulses])+"]]"
				t=time.strftime("%H:%M:%S", time.localtime())
				last=time.strftime("%H:%M:%S", time.localtime(self.shared[const.last_pump_time]))
				status = (f"now: {t}\n"+
					f"last_pump_run_time: {last}\n"+
					f"pump_cycle_reason[{const.cmd[self.shared[const.pump_cycle_reason]]}]\n"+
					f"pump_stopped_reason[{const.cmd[self.shared[const.pump_stopped_reason]]}]\n" +
					f"CURRENT: [{motor}:{flow}]\n"+
					f"pulses in last pulse_collection [{self.shared[const.pulses]}]\n"+
					f"pulses in 5 seconds[{self.shared[const.pulses_in_5_seconds]}]\n"+
					f"flow L/m [{float(self.shared[const.ltr_per_minute])}]")
					
				_data = json.dumps({"color":color, "status":status})
				yield f"id: 1\ndata: {_data}\nevent: online\n\n"
				#yield f"id: 1\ndata: {status}\nevent: online\n\n"           
				time.sleep(1)
		return Response(respond_to_client(), mimetype='text/event-stream')

if __name__ == "__main__":
	import multiprocessing
	shared = multiprocessing.Array('i', const.shared_size)
	shared[const.pump]=1
	shared[const.flow_switch_state]=1
	shared[const.pulses]=56
	shared[const.flow_start_time]=int(time.time())
	shared[const.last_pump_time]=int(time.time())
	shared[const.last_pump_run_time]=222
	shared[const.pump_cycle_reason]=0
	shared[const.pump_stopped_reason]=0
	flow_commands_q = multiprocessing.Queue(maxsize=2) 
	db_values = multiprocessing.Array('i', const.db_values_size)
	db = database.database(db_values)
	db.load()  
	task(flow_commands_q, shared, db_values)   

