from ipcqueue import posixmq
import const
import time
import threading
import zlib
import json
import sqlite3

class mqtt_task():
    def __init__(self, queue=None, my_parent=None):
    # keep device features updated in the data base 
    # handle the subscribe to the home-broker devices
    # for each subscribe callback compare to previous
    # update differences only NO state information
    import message
    import queue   # python queue not POSIX
    db = sqlite3.connect(const.db_name, timeout=const.db_timeout)
	check = check_and_refresh_devices(db)	
    q = queue.Queue() # callbacks are sent here
    msg = message.message(q) # MQTT connection tool# 

    msg.subscribe(const.home_MQTT_devices)
    #msg.publish(const.zigbee2mqtt_bridge_devices, 
    while True:
        (action, topic, payload) = q.get()
        if (action == "callback"):
            if (topic == const.home_MQTT_devices):
                check.compare_and_update(payload)
            else: # other topics are from device subscribes
                update_device_state(db,topic,payload)



    msg.publish("message_unit_test/demo_wall/set", '{"state": "on"}')
    msg.subscribe("message_unit_test/demo_wall/#")
    time.sleep(2) # prettier  output
    # this handles callbacks from above

class check_and_refresh_devices():
    def __init__(self, db):
		self.db = db
	    self.previous = None
		self.topic_to_device_feature = {}
		self.FEATURES = "features"

	def compare_and_update(self, payload):
		unzipped = zlib.decompress(payload)
		self.current = json.loads(unzipped)
		if previous_devices_dictionary == None:
			self.previous = self.current
		print(self.current)
		for friendly_name in (self.current.keys()):
			print(friendly_name)
			if friendly_name in self.previous:  # exists
				if (self.current[friendly_name]['description'] != self.previous[friendly_name]['description'] or
				   self.current[friendly_name]['date']         != self.previous[friendly_name]['date'] or
				   self.current[friendly_name]['source']       != self.previous[friendly_name]['source']):
				   update_device(friendly_name, self.current);
				if FEATURES in self.current[friendly_name]:  # has features check for changes
					for feature in (self.current[friendly_name][FEATURES].keys()):  # each feature
						print("\t", feature)
						current_feature =   self.current[friendly_name][FEATURES][feature]
						previous_feature = self.previous[friendly_name][FEATURES][feature]
						print(current_feature)
						for tag in (current_feature.keys():
							if current_feature[tag] != previous_feature[tag]:
								update_feature(friendly_name, feature, current_feature);
			else:
				insert_device(friendly_name, self.current)

	def insert_device(self,friendly_name, current):
		print(device)
		
	def update_device(self,friendly_name, current):
		print(device)                 
		
	def update_feature(self, friendly_name, feature, current_feature);
		# we build/rebuild the subscribed topic_to_device_feature
		# used when subscribe callbacks arrive
		targets = []
		if (current_feature["access"] == "sub":
			if current_feature["topic"] in self.topic_to_device_feature: 
				targets = self.topic_to_device_feature[current_feature["topic"]]
			targets.append([friendly_name, feature])
			self.topic_to_device_feature[current_feature["topic"]] = targets
		print(friendly_name, current_feature)
		# now update feature

class device_state(db):
    def __init__(self, db):
		self.db = db	
	def update(self, topic, state):
    	pass
		
#list_all_devices(devices_dictionary)


# simple device dump/print
# # designed to load/update two tables
# a devices table and a features table
# a device has 1 or more features.
# Each feature contains the proper pub/sub strings
# no status information is included or ever will be.  
def list_all_devices(dev):
    all_devices = dev["devices"]
    print("\nDEVICES\n")
    for d in all_devices:
        print(d)
    print("\nFEATURES\n")
    all_features = dev["features"]
    for f in all_features:
        print(f)
if __name__ == "__main__":
    mqtt_task()
