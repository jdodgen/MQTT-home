# MIT licence Jim Dodgen 2024
# Jim's install tool, pushes files, usualy python to remote hosts
# see home-broker for example
#
# list of hosts to push one or all files to
#
hosts = [
"192.168.0.193",
"home-broker.local",
]
#
# list of files to send
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
#
# code starts here.
import pysftp
import os

print("0 - all hosts")
ndx = 1
for h in hosts:
    print("%s - %s" % (ndx,h,))
    ndx += 1
print("which?")
i = input()
name="jim"
word="foobar"
if int(i) == 0:
    what_to_do = hosts
else:
    try:
        what_to_do = [hosts[int(i-1)],] # singleton
    except:
        print("Not a valid entry, must be 0 to %s" % (len(hosts)+1,))
    else:
        for host in what_to_do:
            print("uploading to %s@%s" % (name, host,)) # I force access to the code for the password
            try:
                with pysftp.Connection(host, username=name, password=word) as sftp:
                    print("pushing files ...")
                    for f in files:
                        sftp.put(f)
            except: 
                print("An error occured, typicaly cert issue,\nrunning ssh to clean it up\n")          
                os.system("ssh %s@%s" % (name,host,))
            

