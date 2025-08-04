# MIT license copyright 2024,25 Jim Dodgen
# this configures and installs software
# it replaces the cfg.py file each time it runs
# Y N defaults are designed for rapid deployment during development
# usage is: "python3 install.py cluster_example.toml"
cluster_example_toml='''
# this is a toml configuration file see https://toml.io/
# this file is used by install.py to generate device cfg.py files

cluster_id = "your place"  # as in: "/home/your place/Big Generator/power"

[network]
ssid =  "mywifi"
wifi_password = '12345678'

[mqtt_broker]
broker="home-broker.local"  # or where ever your MQTT broker is
ssl = true/false
user = "user"
password = "password"

[email]
to_list = ["foo@bar.com", "bar@foo.com"]
gmail_password = "xxx xxx xxx xxx"
gmail_user = "??@gmail.com"

[sensor]
#  do not use slashes "/" or "+" in the "name". It messes with the MQTT wild cards
#  email = true means that the sensor sends emails when sensors lost and found
[sensor.G]
desc = "Generator powered outlet" # Typically in gally/kitchen in plain sight
email = true  # if false this sensor does not send emails
[sensor.U]
desc = "Utility power company"
email = true
[sensor.3]
id = "S"
soft_tracking = true  # not monitored at boot only after a publish
name = "solar_batteries"
email = false
[sensor.3]
id = "R"
desc = "Offsite monitor"
email = false
ssid = "otherwifi"
wifi_password = "otherpw"
[sensor.E]
desc = "passive watcher"
monitor_only = true  # this only subscribes and does NOT publish a status. it is soft_tracking by default
send_email = true
'''

import os
from pathlib import Path
import datetime
import tomllib
import sys

# change these as needed
mp_lib_offset="../../library/"  # micropython specific
all_lib_offset="../../../library/" # both linux and micropython
cluster_lib = str(Path.home())+"/Dropbox/wip/pcn_clusters"

if os.name == 'nt':
    serial_port = "COM3"
else: # linux
    serial_port = "/dev/ttyACM0"
print("Device on:", serial_port)

# for imports from libraries we need to do this:
# Get the absolute path of the current script's directory
# Add the parent directory to sys.path
# In this example, if main.py is in 'project/', this adds 'project/'
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, all_lib_offset))
import feature_power # located in all_lib_offset
# end of stuff that needs modification

def load_cluster(cluster_file_name):
	if len(cluster_file_name) > 1:
		cluster_toml = cluster_lib+"/"+cluster_file_name
	else:
		print("testing from current directory")
		cluster_toml = "cluster-example.toml"  # test cluster
	try:
		with open(cluster_toml, 'rb') as toml_file:
			cluster = tomllib.load(toml_file)
			return cluster
				# print(cluster)
	except FileNotFoundError:
		print("Error: ",cluster_toml," File not found")
		sys.exit()
	except tomllib.TOMLDecodeError as e:
		print("Error: Invalid TOML format in {file_path}: {e}")
		sys.exit()

def print_sensors(sensors):
    sensor_keys = list(sensors.keys())
    sensor_keys.sort()
    for key in sensor_keys:
        #print("sensor key=", key)
        if len(key) != 1:
            print("id [%s] mist be a single letter or number" % (key, ))
        try:
            desc =sensors[key]["desc"]
        except:
            desc=""
        print("%s) %s" % (key, desc))
        if(('+' in desc) or ('/' in desc) or ('+' in key) or ('/' in key)):
            print("\nERROR: future topic  [%s][%s] contains a / or +,  MQTT reserved fix in toml file\n" % (key,desc,))
            sys.exit()

class create_cfg:
	def __init__(cluster, sensor_to_make):
		self.cluster = cluster
		self.sensor_to_make = sensor_to_make
		self.sensors = self.cluster["sensor"]
		self.set_cfg_values()
		self.write_cfg()

	def set_cfg_values(self,):
		if sensor_to_make in sensor_to_makesensors:
			desc = self.sensors[self.sensor_to_make].get("desc")
			self.publish_to = self.sensor_to_make+" "+desc if desc else self.sensor_to_make
			self.send_email = self.sensors[self.sensor_to_make].get("send_email",False)
			self.ssid = sensors[sensor_to_make].get("ssid", cluster["network"]["ssid"])
			self.wifi_password = self.sensors[sensor_to_make].get("wifi_password", cluster["network"]["wifi_password"])
			self.monitor_only = sensors[sensor_to_make].get("monitor_only", False)
			self.switch = sensors[sensor_to_make].get("switch", False)
			self.switch_type = sensors[sensor_to_make].get("switch_type","NO")
		else:  # these "letters" do not exist in the toml file but are treated as "soft_tracking"  that is not tracked until first publish
			self.publish_to = sensor_to_make   # single letter version
			self.send_email = False
			self.ssid = cluster["network"]["ssid"]
			self.wifi_password = cluster["network"]["wifi_password"]
			self.monitor_only = False
			self.switch = False
			self.switch_type = False
		print("publish_to [%s] send_email [%s] ssid[%s] pw[%s] monitor_only [%s] switch [%s] switch_type [%s]" %
			(self.publish_to, self.send_email, self.ssid, self.wifi_password, self.monitor_only, self.switch, self.switch_type))
		self.email_addresses()

	def make_topic(self):
		#if sensor_to_make in self.sensors:
		self.desc = self.sensors.get(sensor_to_make, "")
			# if "desc" in self.sensors[sensor_to_make]:
				# desc = self.sensors[sensor_to_make]["desc"]
			# else:
				# desc = ''
			# else:
				# desc = ''
		if self.desc == '':
			return cluster["cluster_id"]+"/"+self.sensor_to_make
		else:
			return cluster["cluster_id"]+"/"+self.sensor_to_make+" "+self.desc
		self.our_feature = feature_power.feature(make_topic_cluster_pub(publish_to), publish=True)   # publisher
		print(self.our_feature.topic())

		# build features
		#our_feature    = feature_power.feature(make_topic_cluster_pub(publish_to), publish=True)   # publisher
		# print(our_feature.topic())
		
	def email_addresses(self):
		self.cc_string = ''
		for addr in self.cluster["email"]["to_list"]:
			self.cc_string += "<%s>," % (addr,)
		self.cc_string = self.cc_string.rstrip(",")
		print(self.cc_string)
		return self.cc_string

	# cc_string = email_addresses(cluster)

	def create_hard_tracked_topics(self):
		sensor_keys = list(self.sensors.keys())
		self.hard_tracked_topics = [] # these get tracked from boot. others (soft) only after first publish
		for key in sensor_keys:
			if self.sensors[key].get("soft_tracking") == True or self.sensors[key].get("monitor_only") == True:
					continue
			self.hard_tracked_topics.append(feature_power.feature(self.make_topic(key), subscribe=True).topic())

		#hard_tracked_topics = create_hard_tracked_topics(sensors, sensor_keys)

		print("hard tracked topics", hard_tracked_topics)

#print("\nflashing ssid[%s] device[%s]\n" % (ssid, publish_to,))

# this is the cfg.py template uses % to pass in stuff
	def write_cfg(self):
		cfg_template = """
# MIT license copyright 2024, 2025 Jim Dodgen
# this cfg.py was created by: install.py
# Date: %s
# MAKE YOUR CHANGES IN install.py
#
led_gpio = 3  # "D3" on D1-Mini proto card
onboard_led_gpio = 15 # built in BLUE led
switch_gpio = 18 # only used when "switch = True"
#
#wifi: IoT or guest network recomended
ssid="%s"
wifi_password = "%s"
#
#
start_delay=0 # startup delay
number_of_seconds_to_wait=30  # Alive message published and "missing sender search" conducted at this rate
other_message_threshold=4  # how many number_of_seconds_to_wait to indicate other is down
#
broker = '%s'
ssl = %s # true or false
user = '%s'
password = '%s'
#
# a python list of one or more email addresses ["9095551212@tmomail.net", "you@gmail.com"]
send_messages_to = %s # a python list
#
# gmail account to send emails through
#
gmail_password = "%s" # gmail generates this and it can change it in the future
gmail_user = "%s"
cc_string = "%s"  # a smtp Cc: string

publish = "%s"
cluster_id = "%s"
send_email =  %s
hard_tracked_topics = %s # these get tracked from boot, others only after first publish
monitor_only = %s  # if True this sensor does not publish status and therefore is not tracked
switch = %s # if true then "switch_gpio" is tested if off then no publish will be sent
switch_type = "%s" # for "NO or NC defaults to "NO". So when "closed" no "power" publishes are sent
"""
		now = datetime.datetime.now()
		cfg_text =  cfg_template % (now.strftime("%Y-%m-%d %H:%M:%S"),
			self.ssid,
			self.wifi_password,
			self.cluster["mqtt_broker"]["broker"],
			self.cluster["mqtt_broker"]["ssl"],
			self.cluster["mqtt_broker"]["user"],
			self.cluster["mqtt_broker"]["password"],
			self.cluster["email"]["to_list"],
			self.cluster["email"]["gmail_password"],
			self.cluster["email"]["gmail_user"],
			self.cc_string,
			self.publish_to,
			self.cluster["cluster_id"],
			self.send_email,
			self.hard_tracked_topics,
			self.monitor_only,
			self.switch,
			self.switch_type)
		#print("[%s][%s] [%s]\n%s [%s][%s]\n" % (ssid, wifi_password, broker, to_list,
		#   gmail_password, gmail_user ))
		with open('cfg.py', 'w') as f:
			f.write(cfg_text)
		print("created cfg.py")

cluster = load_cluster(sys.argv[1])
print_sensors(cluster["sensor"])
print("select one (case insensitive): ", end="")
sensor_to_make = input().upper()
print("request = ", sensor_to_make)
create_cfg(cluster, sensor_to_make) # drops cfg.py file

# install micropython kernal
did_we_flash = False
print ("press and hold O (flat side)\nthen press RST (indent) momentary\nrelease O\nto allow flashing micropython")
print("install micropython? (y,N)")
ans = input()
if (ans.upper() == "Y"):
    did_we_flash = True
    os.system("esptool.py --port /dev/ttyACM0 erase_flash")
    # os.system("esptool.py --chip esp32s2 --port /dev/ttyACM0 write_flash -z 0x1000 ESP32_GENERIC_S2-20241129-v1.24.1.bin")
    os.system("esptool.py --chip esp32s2 --port /dev/ttyACM0 write_flash -z 0x1000 ESP32_GENERIC_S2-20250415-v1.25.0.bin")
    print("\npress RST on esp32-s2 to reset (in the indent)")
    input()
# install library code
if did_we_flash == False:
    print("install library code? (y,N)")
    lans = input()
else:
    lans = "Y"
if (lans.upper() == "Y"):
    code = [
    mp_lib_offset+"main.py",
    mp_lib_offset+"boot.py",
    mp_lib_offset+"uuid.py",
    mp_lib_offset+"alert_handler.py",
    mp_lib_offset+"switch.py",
    mp_lib_offset+"umail.py",
    #all_lib_offset+"mqtt_hello.py",
    all_lib_offset+"feature_power.py",
    all_lib_offset+"msgqueue.py",
    mp_lib_offset+"mqtt_as.py",
    ]
    print("now pushing python library code")
    for c in code:
        print("installing", c)
        os.system("ampy --port %s put %s" % (serial_port,c))

# install application code
if did_we_flash == True or lans == "Y":
	 ans = "Y"
else:
    print("\ninstall application code? (Y,n)")
    ans = input()
if (ans.upper() != "N"):
    code = [
    "run.py",
    "cfg.py",
    ]
    print("now pushing python application code")
    for c in code:
        print("installing", c)
        os.system("ampy --port %s put %s" % (serial_port,c))
        
os.system("ampy --port %s ls" % (serial_port,))
if os.name == 'nt':
    print("\n  putty -serial ", serial_port)
else:
    print("\n  picocom -b 115200 ", serial_port)


