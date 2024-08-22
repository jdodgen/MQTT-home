#inside const.py constants and configurable items
#system wide stuff 
version = 0.4

db_name = 'devices.db'
log_path = "/dev/shm/log/"
error_log_path = "log/"
windows_broker = None
mosquitto_file_path = "/etc/mosquitto/mosquitto.conf"
fauxmo_default_dir = "/etc/fauxmo"  

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
# https://www.zigbee2mqtt.io/guide/usage/mqtt_topics_and_messages.html#zigbee2mqtt-bridge-state
zigbee2mqtt_bridge_devices = "zigbee2mqtt/bridge/devices"  # this subscribe gets all the  devices
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

