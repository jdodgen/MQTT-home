import pysftp
# import os
host = "192.168.0.213"  # hot water
name="jim"
word="foobar"
print("uploading to %s@%s" % (name,host,)) # I force access to the code for the password
with pysftp.Connection(host, username=name, password=word) as sftp:
    print("pushing files ...")
    sftp.put("src/mqtt_manager.py")
    sftp.put("src/web_server.py")
    sftp.put("src/database.py")
    sftp.put("src/const.py")
    sftp.put("src/detecting_flow_trigger.py")
    sftp.put("src/main.py")
    sftp.put("src/index_html.py")
    sftp.put("src/status_html.py")
    sftp.put("src/flow_event_task.py")
    sftp.put("src/run_pump_cycle.py")
    sftp.put("../../library/mqtt_hello.py")
    sftp.put("../../library/feature_alert.py")
    sftp.put("../../library/feature_button.py")