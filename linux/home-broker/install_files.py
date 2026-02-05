# MIT licence Jim Dodgen 2024
# Jim's install tool, pushes files, usualy python code 
# to one or all remote hosts
# see home-broker for example
#
#
# password and user
name="jim"
word="foobar"
#
# list of hosts to push one or all files to
#
# example:
#["192.168.0.99","your_name","your_password"],
# defaults to "name" and "word" if not a list, 
# just a IP address is all that is needed
# 
hosts = [
["192.168.0.193","jim","foobar"],
"home-broker.local"
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
"src/cfg.py",
"src/timers_daemon.py",
"src/timers_http.py",
"../../library/mqtt_hello.py",   
]
#
# common code starts here.
import pysftp
import os
print("default name[%s] password[%s]" % (name,word))
print("0 - all hosts")
ndx = 1
for h in hosts:
    print("%s - %s" % (ndx,h,))
    ndx += 1

i = input("which? ")

if int(i) == 0:
    what_to_do = hosts
else:
    try:
        what_to_do = [hosts[int(i)-1],] # singleton
    except:
        print("Not a valid index, must be 0 to %s" % (len(hosts),))
        exit(-1)
for h in what_to_do:
    print("uploading to %s" % (h,)) # I force access to the code for the password
    if isinstance(h, list):
        host = h[0]
        user_name = h[1]
        password = h[2]
    else:  # most just be the host
        host = h
        user_name = name # default, set above
        password = word # default, set above
    print("sftp  host[%s] user_name[%s] password[%s]" %(host, user_name, password,))
    try:
        with pysftp.Connection(host, username=name, password=word) as sftp:
            print("pushing files ...")
            for f in files:
                sftp.put(f)
    except: 
        print("An error occured, typicaly cert issue,\nrunning ssh to clean it up\n")          
        os.system("ssh %s@%s" % (name,host,))
