import pysftp
import os
hosts = [
"192.168.0.193",
"home-broker.local",
]
ndx = 0
for h in hosts:
    print("%s) %s" % (ndx,h,))
    ndx += 1
print("which host? (0-%s)" % (ndx-1,))
i = input()
name="jim"
word="foobar"
host=hosts[int(i)]
print("uploading to %s@%s" % (name, host,)) # I force access to the code for the password

files = [
"src/zigbee2mqtt_manager.py",
"src/mqtt_service_task.py",
"src/http_server.py",
"src/database.py",
"src/fauxmo_manager.py",
"src/mosquitto_manager.py",
"src/const.py",
"src/message.py",
"src/devices_to_json.py",
"src/load_zigbee_data.py",
"src/mqttplugin.py",
"src/load_IP_device_data.py",
"src/main.py",
"src/json_tools.py",
"src/index_html.py",
"../../library/mqtt_hello.py",   
]

try:
    with pysftp.Connection(host, username=name, password=word) as sftp:
        print("pushing files ...")
        for f in files:
            sftp.put(f)
except: 
    print("An error occured, typicaly cert issue,\nrunning ssh to clean it up\n")          
    os.system("ssh %s@%s" % (name,host,))

