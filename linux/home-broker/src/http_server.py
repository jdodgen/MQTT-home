from gevent import monkey; monkey.patch_all()
from flask import Flask, render_template_string,  request
from gevent.pywsgi import WSGIServer
import os
import database
import load_zigbee_data
import fauxmo_manager
import const
import message
import threading
import paho.mqtt.subscribe as subscribe
#import multiprocessing
from queue import Empty
import time
import index_html
import mqtt_hello
#
# conditional print
import os 
my_name = os.path.basename(__file__).split(".")[0]
xprint = print # copy print
def print(*args, **kwargs): # replace print
    #return
    xprint("["+my_name+"]", *args, **kwargs) # the copied real print
#
#
app = Flask(__name__)
shared=[]
q=True
btc=None
db=None
db_values=None
fauxmo_task = None
watch_dog_queue = None


##############################
app.debug = True
def debug():
    print("Request Headers %s" % (request.headers,))
    return None

@app.route("/")
def render_index():
    print("getting index.html")
    return render("")  

@app.route("/whoareyou")
def whoareyou():
    myhost = os.uname()[1]
    print("host name ", myhost)
    return "iam/"+myhost

@app.route("/password", methods =["GET", "POST"])
def create_password():
    if request.method == "POST":
        pw = request.form["password"]
        db.replace_password(pw)

@app.route("/create_wemo", methods =["GET", "POST"])
def create_wemo():
    error_msg = ''
    print("entering create_wemo[%s]" % (request.method,))
    global fauxmo_task
    global db
    global watch_dog_queue
    if request.method == "POST":
        print("got post")
        action = request.form["action"]
        print("action[%s]" % action)
        if action == "restart":
             watch_dog_queue.put(["startfauxmotask", "start"]) # cause a restart
        elif action == "display":
            cfg = fauxmo_manager.get_fauxmo_cfg()
            if cfg:
                return render_template_string("<pre>%s</pr>" % (cfg,))
            else:
                error_msg = "No wemo devices found"
        else:
            if "wemo_name" in request.form and "wemo_device" in request.form:
                print("create_wemo  form[%s]" % request.form)
                port = request.form["wemo_port"]
                print("create_wemo  port[%s]" % port)
                name = request.form["wemo_name"]
                device = request.form["wemo_device"]
                if port in ("Optional", None):
                    port = None 
                print("CREATE_WEMO name[%s] device[%s] port[%s]" % (name, device, port,))  
                status = db.create_wemo(name, port, device)  
                if (not status):
                    error_msg = "error inserting"
            else:
                error_msg = 'Both wemo name and device required, port is optional and usually auto assigned'
    return render(error_msg) 

@app.route("/modify_wemo", methods =["GET", "POST"])
def modify_wemo():
    print("modify_wemo called")
    global db
    if request.method == "POST":
        error_msg = ''
        print(request.form)	
        action = request.form["action"]
        print("action",action)	
        thing, rowid = request.form["action"].split("/")
        print("modify_device_broker thing[%s] rowid[%s]" % (thing, rowid))
        db.delete_wemo(rowid)
    return render(error_msg)

@app.route("/all_devices", methods =["GET", "POST"])
def all_devices():
    msg = ""
    if request.method == "POST":
        global db
        rowid=None
        update_IP = False
        print("/all_devices action[%s]" % request.form["action"])
        parts = request.form["action"].split("/")
        print("/all_devices action part 0 [%s]" % parts[0])
        if parts[0] == "send":
            send_mqtt_publish(parts[2], parts[1])
        elif parts[0] == "zbrefresh":
            subscribe.simple(const.zigbee2mqtt_bridge_devices, hostname=message.our_ip_address())
            # message.simple_subscribe(const.zigbee2mqtt_bridge_devices)
            msg="ZigBee devices refreshing"
        elif parts[0] == "iprefresh":
            message.publish_single(mqtt_hello.hello_request_topic, my_name) 
            msg="Auto IP devices refreshed"
        elif parts[0] == 'delete':
            db.delete_device(parts[1])
        elif parts[0] == "manIP":
            update_IP = True
            rowid = parts[1]
        else:
            msg="unknown request"
    return render(msg, update_ip=update_IP,manIP_rowid=rowid)

@app.route("/update_manIP", methods =["GET", "POST"])
def update_manIP( ):
    print("update_manIP called")
    global db
    if request.method == "POST":
        (cmd,id) = request.form["action"].split("/")
        if cmd == "Update":
            db.update_manIP_feature(  
                request.form["type"],
                request.form["access"],
                request.form["topic"],
                request.form["on"],  
                request.form["off"],
                id, 
                )
        elif cmd == "delete":
            db.delete_device(id)
    return render("")  

@app.route("/create_IP_device", methods =["GET", "POST"])
def create_IP_device():
    if request.method == "POST":
        global db
        error=''
        name = request.form["IP_name"]
        desc = request.form["IP_description"]
        print("create_IP_device", name, desc)
        if name and desc:
            db.upsert_device(desc, name, "manIP")
        else:
            error = "Both name and description needed"  
    return render(error)   

@app.route("/create_IP_feature", methods =["GET", "POST"])
def create_IP_feature():
    if request.method == "POST":
        global db
        print(
        request.form["property"],
        request.form["device_ieee_address"])
        db.upsert_feature(
            request.form["device_ieee_address"] ,
            request.form["property"],
            None, 
            "binary",
            "", 
            None,  
            'on',  
            'off')		  
    return render("")  

        
def render(error, update_ip=False, manIP_rowid=None):
    print("http_server.render called")
    return render_template_string(index_html.html, 
        error_message = error,
        do_update_IP = update_ip,
        man_ip = db.get_manIP_device(manIP_rowid),
        manIP_devices =  db.cook_devices_features_for_html(source='manIP'),
        autoIP_devices = db.cook_devices_features_for_html(source='IP'),
        zigbee_devices = db.cook_devices_features_for_html(source='ZB'),
        get_devices_for_wemo = db.get_devices_for_wemo(),
        all_wemo = db.get_all_wemo(),
        manual_device_names = db.get_all_manual_device_names()
        ) 

def send_mqtt_publish(feature_rowid, true_or_false):
    print("send_mqtt_publish rowid[%s] [%s]" % (feature_rowid, true_or_false))
    (access, 
    topic, 
    true_value, 
    false_value, 
    ) = db.get_feature_mqtt(feature_rowid)
    if true_or_false ==  "1":
        payload = true_value
    else:
        payload = false_value
    message.publish_single(topic, payload, my_parent=my_name)

# def mqtt_task(mqtt_queue):
#     print("http_server.mqtt_task starting", type(mqtt_queue))
#     m=message(mqtt_queue, my_parent=my_name)
#     while True:
#         try:
#             item = mqtt_queue.get(timeout=const.mqtt_keepalive)
#         except Empty:
#             print("http_server.mqtt_task mqtt_queue timed out")
#             continue

#         cmd = item[0]
#         print("http_server.mqtt_task dequeued", item)
#         if cmd == "subscribe":
#             m.subscribe(item[1])
#         elif cmd == "publish":
#             print("http_server.mqtt_task publishing[%s][%s]" % (item[1], item[2]))
#             m.publish(item[1], item[2])



def task(fauxmo, watch_dog_queue_in):
    global fauxmo_task
    global db
    global watch_dog_queue
    watch_dog_queue = watch_dog_queue_in
    fauxmo_task = fauxmo
    # os.nice(-1)
    db=database.database()
    print("Starting http server...")
    http_server = WSGIServer(("0.0.0.0", const.http_port), app)
    #print("Starting http server serve_forever")
    http_server.serve_forever()
    print("http_server.serve_forever we should not get here")

def start_http_task(fauxmo, watch_dog_queue):
    http_thread = threading.Thread(target=task, args=[fauxmo, watch_dog_queue])
    http_thread.start()
    return http_thread

def stop_http_task(p):
    p.terminate()
    while p.is_alive():
        print("http wont die")
        time.sleep(0.1)
    p.join()
    p.close()

# unit test
if __name__ == "__main__":
    from queue import Queue
    q =Queue()
    http_thread = None
    while True:
        if not http_thread or not http_thread.is_alive():
            http_thread = start_http_task("fauxmo", q)
            print("watchdog http_thread needs to be started")
        else:
            pass
        #print("watchdog http_thread running")
        time.sleep(10)
