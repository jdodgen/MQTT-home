import pysftp
#host = "192.168.0.193"
host = "192.168.1.226"
name="jim"
word="foobar"
print("uploading to %s@%s" % (name,host,)) # I force access to the code for the password
# os.system("sshpass -p foobar sftp -oBatchMode=no -b install_files.bat "+target)
with pysftp.Connection(host, username=name, password=word) as sftp:
    print("pushing files ...")
    sftp.put("src/zigbee2mqtt_manager.py")
    sftp.put("src/mqtt_service_task.py")
    sftp.put("src/http_server.py")
    sftp.put("src/database.py")
    sftp.put("src/fauxmo_manager.py")
    sftp.put("src/mosquitto_manager.py")
    sftp.put("src/const.py")
    sftp.put("src/message.py")
    sftp.put("src/devices_to_json.py")
    sftp.put("src/load_zigbee_data.py")
    sftp.put("src/mqttplugin.py")
    sftp.put("src/load_IP_device_data.py")
    sftp.put("src/main.py")
    sftp.put("src/json_tools.py")
    sftp.put("src/index_html.py")
    sftp.put("../../library/mqtt_hello.py")