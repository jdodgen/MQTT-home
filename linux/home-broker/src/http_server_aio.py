import os
import jinja2
import aiohttp_jinja2
from aiohttp import web
import database
import const

db=database.database()

# Global placeholders from your snippet
#shared, q, btc, db_values = [], True, None, None, None
fauxmo_task, watch_dog_queue = None, None

# 1. Helper to replace your 'render' function
async def render_response(request, error, update_ip=False, manIP_rowid=None):
    global db
    # This replaces your 'render' function and uses the Jinja2 engine
    context = {
        "error_message": error,
        "do_update_IP": update_ip,
        "man_ip": db.get_manIP_device(manIP_rowid),
        "manIP_devices": db.cook_devices_features_for_html(source='manIP'),
        "autoIP_devices": db.cook_devices_features_for_html(source='IP'),
        "zigbee_devices": db.cook_devices_features_for_html(source='ZB'),
        "get_devices_for_wemo": db.get_devices_for_wemo(),
        "all_wemo": db.get_all_wemo(),
        "manual_device_names": db.get_all_manual_device_names(),
        "IPaddr": const.IPaddr
    }
    # This renders the template named 'index.html'
    return aiohttp_jinja2.render_template('index.html', request, context)

# 2. Define Route Handlers
async def render_index(request):
    print("getting index.html")
    # return aiohttp_jinja2.render_template('index.html', request, {})
    return await render_response(request, "")
    
async def create_IP_device(request):
    if request.method == "POST":
        global db
        data = await request.post()
        action = data.get("action")
        error_msg=''
        name = data["IP_name"]
        desc = data["IP_description"]
        print("create_IP_device", name, desc)
        if name and desc:
            db.upsert_device(desc, name, "manIP")
        else:
            error_msg = "Both name and description needed"  
    return await render_response(request, error_msg) 
         
async def create_IP_feature(request):
    print("update_manIP called")
    global db
    error_msg = ''
    if request.method == "POST":
        data = await request.post()
        action = data.get("action")
        print("action", action)
        (cmd,id) = action.split("/")
        # (cmd,id) = request.form["action"].split("/")
        if cmd == "create_wifi":
            db.update_manIP_feature(  
                data["type"],
                data["access"],
                data["topic"],
                data["on"],  
                data["off"],
                id, 
                )
        elif cmd == "delete":
            db.delete_device(id)
    return await render_response(request, error_msg)  

async def whoareyou(request):
    myhost = os.uname()[1]
    return web.Response(text=f"iam/{myhost}")

async def create_wemo(request):
    error_msg = ''
    # aiohttp requires awaiting the form data
    if request.method == "POST":
        data = await request.post()
        action = data.get("action")
        if action == "restart":
             watch_dog_queue.put(["startfauxmotask", "start"])
        elif action == "display":
            cfg = "fauxmo_cfg_placeholder" # Replace with your manager call
            return web.Response(text=f"<pre>{cfg}</pre>", content_type='text/html')
        else:
            if "wemo_name" in data and "wemo_device" in data:
                db.create_wemo(data["wemo_name"], data.get("wemo_port"), data["wemo_device"])
            else:
                error_msg = 'Both wemo name and device required'
    
    return await render_response(request, error_msg)
    
async def all_devices(request):
    msg = ""
    if request.method == "POST":
        global db
        rowid=None
        update_IP = False
        data = await request.post()
        print("/all_devices action[%s]" % data["action"])
        action = data.get("action", "")
        parts = action.split("/")
        ## parts = request.form["action"].split("/")
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
    return await render_response(request, msg, update_ip=update_IP, manIP_rowid=rowid)
    # return render(msg, update_ip=update_IP,manIP_rowid=rowid)

# async def all_devices(request):
    # msg = ""
    # update_IP = False
    # rowid = None
    # if request.method == "POST":
        # data = await request.post()
        # action = data.get("action", "")
        # parts = action.split("/")
        # if parts[0] == 'delete':
            # db.delete_device(parts[1])
        # elif parts[0] == "manIP":
            # update_IP = True
            # rowid = parts[1]
    # return await render_response(request, msg, update_ip=update_IP, manIP_rowid=rowid)

# 3. App Setup
app = web.Application()

# Setup Jinja2 (Points to a folder named 'templates')
aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('./templates'))

app.add_routes([
    web.get('/', render_index),
    web.get('/whoareyou', whoareyou),
    web.get('/create_IP_device', create_IP_device),
    web.post('/create_IP_device', create_IP_device),
    web.get('/create_IP_feature', create_IP_feature),
    web.post('/create_IP_feature', create_IP_feature),
    web.get('/create_wemo', create_wemo),
    web.post('/create_wemo', create_wemo),
    web.get('/all_devices', all_devices),
    web.post('/all_devices', all_devices),
])

def task(fauxmo, watch_dog_queue_in):
    global fauxmo_task
    global db
    global watch_dog_queue
    watch_dog_queue = watch_dog_queue_in
    fauxmo_task = fauxmo
    # os.nice(-1)
    db=database.database()
    print("Starting http server...")
    web.run_app(app, port=const.http_port)
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
if __name__ == '__main__':
    web.run_app(app, port=const.http_port)
