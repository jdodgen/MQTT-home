#inside const.py constants and configurable items
version = 0.3

import os
if os.name =="nt": # testing under Windows
   db_name = 'C:\\Users\\jim\\Dropbox\\wip\\timers\\devices.db'
   log_path = 'C:\\Users\\jim\\log\\'
   error_log_path = 'C:\\Users\\jim\\log\\error\\'
   windows_broker = "home-broker.local"
   #windows_broker = "192.168.0.193"
   mosquitto_file_path = "mosquitto.conf"
   fauxmo_default_dir = "fauxmo"
else: # running as a system under Linux
   db_name = 'devices.db'
   log_path = "/dev/shm/log/"
   error_log_path = "log/"
   windows_broker = "localhost" #None
   mosquitto_file_path = "/etc/mosquitto/mosquitto.conf"
   fauxmo_default_dir = "/etc/fauxmo"  

# import socket
# def get_ip_address():
    # s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # s.connect(("192.168.253.253", 50000))
    # ip =  s.getsockname()[0]
    # s.close()
    # return ip
IPaddr = "192.168.0.138"  #get_ip_address() 
print("Our ip address:", IPaddr)

ifname = b"eth0"  #our network interface, see "ip a" 

fauxmo_config_file_path = fauxmo_default_dir+"/config.json"
fauxmo_sleep_seconds = 120 # wake up every two minutes, Zzzzzz
#
broker_mqtt_port = 1883
#
base_faxmo_port = 56000
mqtt_keepalive = 120
mosquitto_sleep_seconds = 1000 # change when checking for termination in future versions
MQTTPlugin = "mqttplugin.py"
zigbe2mqtt = "zigbee2mqtt"
zigbee_refresh_seconds = 30

http_port = 80  # home-broker note the z2m package uses port 8080
mqtt_service_q_timeout = 60*60*4   # seconds every four hours if it times out then zb/ip devices are refreshed and "home/MQTT_devices" is published
watch_dog_queue_timeout = 20
db_timeout = 120 # we have nothing that would cause a long lock
#
zigbee2mqtt_bridge_devices = "zigbee2mqtt/bridge/devices"  # this subscribe gets all the zigbee devices from z2m 
# 
# home_MQTTdevices_get = "home/MQTTdevices/get"  # topic requests a fresh MQTTDevices 
#
home_MQTT_devices = "home/MQTTdevices/configuration"  # Normalized json of ALL devices.  home-broker "publish reatain"s this for other apps it has all the zb and ip devices unified
#
# hello_subscribe = "home/+/hello" # tgis is a subscribe to capture IP device configs
# 
#
# mosquitto configuration edit this as needed,
# the file is located at mosquitto_file_path
mosquitto_configuration = """
# created by mosquitto_manager.py this is imported in const.py
# go there to make changes and reboot
allow_anonymous true
listener """+str(broker_mqtt_port)+"\nlog_dest none"

