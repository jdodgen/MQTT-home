import os
import jinja2
import aiohttp_jinja2
from aiohttp import web
import aiosqlite
#import database
import re
#import message
#import mqtt_hello
import restart_service
from fauxmo_manager import build_cfg
import http_common as config

MY_IP = config.get_ip() # replaced when forked
DB_NAME =   config.DB_NAME
OUR_PORT =  config.VOICE_PORT
NAV = config.nav_section(raw=True) # replaced when forked
STYLE = config.STYLE

#MAIN_Q=None  #  messages queue

DB=None # built per process
msg=None   # built per process from message.message
# conditional print
import os 
my_name = "vopice_http"
xprint = print # copy print
def print(*args, **kwargs): # replace print
    #return
    xprint("["+my_name+"]", *args, **kwargs) # the copied real print
#

# Global placeholders from your snippet
#shared, q, btc, db_values = [], True, None, None, None
fauxmo_task = None

# 1. Helper to replace your 'render' function
async def render_response(request, error, update_ip=False, manIP_rowid=None):
    global DB
    # This replaces your 'render' function and uses the Jinja2 engine
    # flush the message MAIN_Q 
#    while True:
        # try:
# #            MAIN_Q.get_nowait()
        # except queue.Empty:
            # break
    context = {
        "error_message": error,
        "get_devices_for_wemo": DB.get_devices_for_wemo(),
        "all_wemo": DB.get_all_wemo(),
        "style": STYLE
    }
    # This renders the template named 'index.html'
    return aiohttp_jinja2.render_template('index.html', request, context | NAV)

# 2. Define Route Handlers
async def render_index(request):
    print("getting index.html")
    # return aiohttp_jinja2.render_template('index.html', request, {})
    return await render_response(request, "")
    
# async def create_IP_device(request):
    # error_msg=''
    # if request.method == "POST":
        # global DB
        # data = await request.post()
        # action = data.get("action")
        # name = data["IP_frendly_name"]
        # desc = data["IP_description"]
        # access = None #data["IP_access"]  #sub or pub
        # print("create_IP_device", name, desc)
        # if name and desc: # and access:
            # print("upsert_device")
            # DB.upsert_device(desc, name, "manIP")
            # data_list = {
                # "friendly_name": name, 
                # "property": "manual", #data["IP_property"],
                # "description": desc, #data["IP_feature"],
                # "type": "binary",
                # "access": None, #data["IP_access"],
                # "topic": data["IP_topic"],
                # "true_value": data["IP_true"],
                # "false_value": data["IP_false"],
            # }
            # print("upsert_feature")
            # DB.upsert_feature(data_list)
        # else:
            # error_msg = "Both name description, and access needed"  
    # return await render_response(request, error_msg)  
    
    # global db
    # error_msg = ''
    # if request.method == "POST":
        # data = await request.post()
        # action = data.get("action")
        # print("action", action)
        # (cmd,id) = action.split("/")
        # # (cmd,id) = request.form["action"].split("/")
        # if cmd == "create_wifi":
            # db.update_manIP_feature(  
                # data["type"],
                # data["access"],
                # data["topic"],
                # data["on"],  
                # data["off"],
                # id, 
                # )
        # elif cmd == "delete":
            # db.delete_device(id)
    # return await render_response(request, error_msg)  

# async def z2m_page(request):
    # print("z2m_page")
    # return aiohttp_jinja2.render_template('zigbee2mqtt.html', request, {"IPaddr": MY_IP})

# async def whoareyou(request):
    # myhost = os.uname()[1]
    # return web.Response(text=f"iam/{myhost}")

async def get_voice_row(db_path):
    # 'async with' handles opening and automatically closing the connection
    async with aiosqlite.connect(db_path) as db:
        # Set the row_factory to return Row objects (for column-name access)
        db.row_factory = aiosqlite.Row
        # 'execute' is an async method; use 'async with' to handle the cursor
        async with db.execute("SELECT * FROM config WHERE id = ?", rowid) as cursor:
            # 'fetchone' is also a coroutine and must be awaited
            row = await cursor.fetchone()
        return row
        
async def create_voice(request):
    error_msg = ''
    # aiohttp requires awaiting the form data
    if request.method == "POST":
        data = await request.post()
        action = data.get("action")
        if action == "restart":
            # do a systemd restart to pick up the fresh config
             restart_service.restart("alertaway-fauxmo-task")
             # pre systemd watch_dog_queue.put(["startfauxmotask", "start"])
        elif action == "display":
            cfg = build_cfg()  #"fauxmo_cfg_placeholder" # Replace with your manager call
            return web.Response(text=f"<pre>{cfg}</pre>", content_type='text/html')
        else:
            print(f"Voice[{data}]")
            if "voice_name" in data and "voice_device" in data:
                DB.create_voice(data["voice_name"], data.get("port"), data["voice_device"])
            else:
                error_msg = 'Both Voice name and device required'
    return await render_response(request, error_msg)
    
async def remove_voice(request):
    data = await request.post()
    print(data)
    rowid = data.get("rowid")
    print("rowid", rowid)
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        # 
        async with db.execute("SELECT * FROM voice_device WHERE id=?", (rowid,)) as cursor:
            row = await cursor.fetchone()
            
        await db.execute("DELETE FROM voice_device WHERE id = ?", (rowid,))
        await db.commit()
    if row:
        # Redirect back with query params to pre-fill the form
        return web.HTTPFound(
            f'/?voice_name={row["voice_name"]}&refill_topic={row[1]}&refill_payload={row[2]}'
            f'&refill_subj={row[4]}&refill_body={row[5]}'
        )
    return web.HTTPFound('/')
    
# async def xxxxremove_voice(request):
    # global DB
    # error_msg = ''
    # # aiohttp requires awaiting the form data
    # if request.method == "POST":
        # data = await request.post()
        # action = data.get("action")
        # print("action", action)
        # if "delete_wemo" in action:
            # print("deleteing")
            # match = re.search(r'delete_wemo/(\d+)', action)
            # print("deleteing ", match.group(1))
            # if match:
                # target_id = match.group(1)
                
                # DB.delete_wemo(target_id)
                
                
    # return await render_response(request, error_msg)
    
# async def all_devices(request):
    # error = ""
    # if request.method == "POST":
        # global DB
        # rowid=None
        # update_IP = False
        # data = await request.post()
        # print("/all_devices action[%s]" % data["action"])
        # action = data.get("action", "")
        # parts = action.split("/")
        # ## parts = request.form["action"].split("/")
        # print("/all_devices action part 0 [%s]" % parts[0])
        # if parts[0] == "send":
            # send_mqtt_publish(parts[2], parts[1])
        # elif parts[0] == "zbrefresh":
            # # subscribe.simple(const.zigbee2mqtt_bridge_devices, hostname=message.our_ip_address())
            # msg.subscribe(config.ZIGBEE2MQTT_BRIDGE_DEVICES)
            # error="ZigBee devices refreshing"
        # elif parts[0] == "iprefresh":
            # msg.publish(mqtt_hello.hello_request_topic, my_name) 
            # error="Auto IP devices refreshed"
        # elif parts[0] == 'delete':
            # DB.delete_device(parts[1])
        # elif parts[0] == "manIP":
            # update_IP = True
            # rowid = parts[1]
        # else:
            # error="unknown request"
    # return await render_response(request, error, update_ip=update_IP, manIP_rowid=rowid)
    # # return render(msg, update_ip=update_IP,manIP_rowid=rowid)

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
    
@aiohttp_jinja2.template('voice.html')
async def render_index(request):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM mqtt_feature") as cursor:
            devices_for_voice = await cursor.fetchall()
            for row in devices_for_voice:
                print(dict(row),"\n==================\n")
        #db.row_factory = aiosqlite.Row   
        async with db.execute("SELECT * FROM voice_device") as cursor:
            current_voice = await cursor.fetchall()
            for row in current_voice:
                print("\n-------\n", dict(row),"\n-------------\n")
# 
    return {
    'current_voice': current_voice,
    'devices_for_voice': devices_for_voice,
    'query': request.query,
    "style": STYLE,
    "nav_section": NAV
    }
            
app = web.Application()

# Setup Jinja2 (Points to a folder named 'templates')
aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('./templates'))

app.add_routes([
    web.get('/', render_index),
    web.get('/create_voice', create_voice),
    web.post('/create_voice', create_voice),
    web.get('/remove_voice', remove_voice),
    web.post('/remove_voice', remove_voice),
    # web.get('/all_devices', all_devices),
    # web.post('/all_devices', all_devices),
    # web.get('/zigbee2mqtt', z2m_page),
    # web.post('/zigbee2mqtt', z2m_page),
])

def task(fauxmo):
    global fauxmo_task
    global DB
    global msg
#    global MAIN_Q

    DB=database.database()
    
    MY_IP = config.get_ip() # replaced when forked
    DB_NAME =   config.DB_NAME
    NAV = config.nav_section() # replaced when forked
 #   MAIN_Q = queue.Queue() 
    
#    msg = message.message(MAIN_Q, my_parent=my_name)
    #msg.subscribe(config.ZIGBEE2MQTT_BRIDGE_DEVICES)
    #msg.publish(mqtt_hello.hello_request_topic, my_name)
    fauxmo_task = fauxmo
    # os.nice(-1)
    print("Starting http server...")
    try:
        web.run_app(app, port=OUR_PORT)
        print("http_server.serve_forever we should not get here")
    except Exception as e:
        print("Error during web.run_app:", e)
    
if __name__ == '__main__':
    #DB=database.database()
    web.run_app(app, port=OUR_PORT)
