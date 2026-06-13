import os
import jinja2
import aiohttp_jinja2
from aiohttp import web
from yarl import URL
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
my_name = "voice_http"
xprint = print # copy print
def print(*args, **kwargs): # replace print
    #return
    xprint("["+my_name+"]", *args, **kwargs) # the copied real print
#

fauxmo_task = None

# async def get_voice_row(db_path):
    # # 'async with' handles opening and automatically closing the connection
    # async with aiosqlite.connect(db_path) as db:
        # # Set the row_factory to return Row objects (for column-name access)
        # db.row_factory = aiosqlite.Row
        # # 'execute' is an async method; use 'async with' to handle the cursor
        # async with db.execute("SELECT * FROM config WHERE id = ?", rowid) as cursor:
            # # 'fetchone' is also a coroutine and must be awaited
            # row = await cursor.fetchone()
        # return row
       
@aiohttp_jinja2.template('voice.html')
async def refresh_page(request):
    # Safe check: if it's a GET request, request.post() is empty, which is fine
    form_data = await request.post() if request.method == "POST" else request.query
    error_msg = request.get('error_msg', "")
    
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM mqtt_feature") as cursor:
            devices_for_voice = await cursor.fetchall()
            #for row in devices_for_voice:
                #print(dict(row), "\n==================\n")
          
        async with db.execute('''SELECT 
                    v.id AS voice_device_id,
                    v.voice_name,
                    v.port,
                    v.handler,
                    m.friendly_name,
                    v.topic,
                    v.true_value,
                    m.false_value
                FROM voice_device v
                JOIN mqtt_feature m 
                    ON v.topic = m.topic 
                   AND v.true_value = m.true_value''') as cursor:
            current_voice = await cursor.fetchall()
            #for row in current_voice:
                #print("\n-------\n", dict(row), "\n-------------\n")
    return {
        'error_message': error_msg,
        'current_voice': current_voice,
        'devices_for_voice': devices_for_voice,
        'query': dict(form_data),
        "style": STYLE,
        "nav_section": NAV
    }


@aiohttp_jinja2.template('voice.html')        
async def create_voice(request):
    error_msg = ''
    
    if request.method == "POST":
        data = await request.post()
        action = data.get("action")
        print("----action---", action)
        if action == "restart":
            restart_service.restart("alertaway-fauxmo-task")
        elif action == "display":
            cfg = build_cfg() 
            # Note: Returning a web.Response bypasses the decorator, which is valid here
            return web.Response(text=f"<pre>{cfg}</pre>", content_type='text/html')
        else: # create
            print(f"create [{data}]")
            #print(f'data values in if "{data["voice_name"]}" and "{data.get("device_to_control")}"')
            if data.get("voice_name") and data.get("device_to_control"):
                print(f'processing {data["voice_name"]} -- {data["device_to_control"]}')
                async with aiosqlite.connect(DB_NAME) as db:
                    db.row_factory = aiosqlite.Row
                    async with db.execute("SELECT * FROM voice_device where voice_name = ?", (data['voice_name'],)) as cursor:
                        voice_name = await cursor.fetchone()
                        if voice_name:  # exists
                                error_msg = f'Choose different name, "{data["voice_name"]}" exists'
                        else:
                            print(f'name ok now checking port "{data["port"]}"')
                            port = int(data['port']) if data.get('port', '').strip() else 0 
                            print(f'int conversion  port {port}')
                            if port == 0:
                                print("port == 0 so creating one")
                                async with db.execute("SELECT coalesce(max(port), 0) as max_port FROM voice_device") as cursor:
                                    max_port = await cursor.fetchone()
                                    print(dict(max_port))
                                    port = max_port["max_port"] + 1
                                    print (f'new port {port}')
                            else:
                                pass
                            async with db.execute("SELECT * FROM voice_device where port = ?", (port,)) as cursor:
                                port_exists = await cursor.fetchone()
                                if port_exists: # exists
                                    error_msg = f'Choose another port, {port} exists'
                                else:
                                    async with db.execute("SELECT * FROM mqtt_feature  WHERE id = ?", (data["device_to_control"],)) as cursor:
                                        mqtt_feature = await cursor.fetchone()
                                    print(f"inserting {data['voice_name']}")
                                    await db.execute('''INSERT INTO voice_device (
                                        voice_name, 
                                        port, 
                                        handler, 
                                        topic, 
                                        true_value) 
                                        VALUES (?,?,?,?,?)''',
                                     (data['voice_name'],
                                     port,
                                     data.get('handler',"wemo"),
                                     mqtt_feature['topic'],
                                     mqtt_feature['true_value'],
                                     ))
                                    await db.commit()
            else:
                error_msg = 'Both Voice name and device are required'
                
    # Pass the error down into the request context dictionary
    request['error_msg'] = error_msg
    
    # Call refresh_page to get the baseline dictionary context
    context_data = await refresh_page(request)
    
    # Return JUST the dictionary. The decorator automatically handles the template rendering!
    return context_data
  
async def remove_voice(request):
    data = await request.post()
    print(data)
    rowid = data.get("rowid")
    print("rowid", rowid)
    
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        
        # Keep your select query to fetch the row before deletion
        async with db.execute("SELECT * FROM voice_device WHERE id=?", (rowid,)) as cursor:
            row = await cursor.fetchone()
            
        await db.execute("DELETE FROM voice_device WHERE id = ?", (rowid,))
        await db.commit()
        
    if row:
        # Note: Replaced numeric indices (row[2]) with actual column names 
        # since you are using aiosqlite.Row. Adjust these column names to match your schema!
        query_params = {
            'voice_name': row["voice_name"],
            'port': row["port"],
            #'refill_payload': row["handler"],      # e.g., mapping old row[2] index
            #'refill_subj': row["friendly_name"],   # e.g., mapping old row[4] index
            #'refill_body': row["topic"],            # e.g., mapping old row[5] index
        }
        
        # Build the redirect target link cleanly
        clean_params = {k: (v if v is not None else "") for k, v in query_params.items()}
        print(f'clean parms {clean_params}')
        redirect_url = URL('/').with_query(clean_params)
        return web.HTTPFound(redirect_url)
        
    return web.HTTPFound('/')


# starting up             
app = web.Application()
# Setup Jinja2 (Points to a folder named 'templates')
aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('./templates'))

app.add_routes([
    web.get('/',  refresh_page),
    web.get('/create_voice', create_voice),
    web.post('/create_voice', create_voice),
    web.get('/remove_voice', remove_voice),
    web.post('/remove_voice', remove_voice),
])
    
if __name__ == '__main__':
    web.run_app(app, port=OUR_PORT)
