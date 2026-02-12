# MIT licence copyright 2026 Jim Dodgen

import re
# import aiosqlite
import multiprocessing
import aiohttp_jinja2
import jinja2
from aiohttp import web
from datetime import datetime
import database
import const

watch_dog_queue = None
xprint = print # copy print
my_name = "[trigger_http]"
def print(*args, **kwargs): # replace print
    #return  # comment/uncomment to turn print on off
    # do whatever you want to do
    #xprint('statement before print')
    xprint(my_name, *args, **kwargs) # the copied real print


# --- DATABASE SETUP ---
async def init_db(app):
    # Open connection once at startup
    db = database.database(row_factory=True)
    #  best to stay with one sqlite instance  not using ### db = await aiosqlite.connect("automation.db")
    # db.row_factory = aiosqlite.Row  # Access columns by name: row['desc']
    app['db'] = db
    
async def close_db(app):
    app['db'].close()

# --- THE MAIN HANDLER ---
async def trigger_manager(request):
    global watch_dog_queue
    db = request.app['db']
    context = {
        "triggers_here": "here",
        "triggers_msg": "",
    }
    # 1. Handle Form Actions (POST)
    if request.method == "POST":
        form = await request.post()
        print("form\n", form)
        action = form.get("action", "")
        print("action [%s]" % (action,))
        # Logic for "Set timer"
        if action == "Create trigger":
            selected_pub = form.get("selected_pub")
            selected_sub = form.get("selected_sub")
            print("selected_pub", selected_pub)
            print("selected_sub", selected_sub)
            if selected_pub and selected_sub:
                (pub_topic, pub_payload) = selected_pub.split("|")
                (sub_topic, sub_payload) = selected_sub.split("|")
                db.con.execute("""
                    INSERT INTO triggers (
                        sub_topic, sub_payload, pub_topic, pub_payload
                    ) VALUES (?, ?, ?, ?)
                """, (
                    sub_topic,
                    sub_payload,
                    pub_topic, 
                    pub_payload
                ))
                db.con.commit()
            else:
                context["trigger_msg"] = "ERROR:  you need a pub and a sub"
        # Logic for "Remove Timer"
        elif "Remove Trigger:" in action:
            print(action)
            match = re.search(r'Remove Trigger:(\d+)', action)
            if match:
                target_id = match.group(1)
                db.con.execute("DELETE FROM triggers WHERE rowid = ?", (target_id,))
                db.con.commit()
        elif action == "Restart trigger Process":
            watch_dog_queue.put(["restarttriggertask", "restart"])

    #cursor = db.execute("SELECT * FROM devices") # Adjust table name as needed
    context['pubs'] = db.get_publish_devices() 
    context['subs'] = db.get_subscribe_devices() 
    context['current_triggers'] = db.get_all_triggers()
    context["IPaddr"] = const.IPaddr

    return aiohttp_jinja2.render_template('trigger.html', request, context)

# --- APP ROUTING ---
app = web.Application()
aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('./templates'))

app.on_startup.append(init_db)
app.on_cleanup.append(close_db)

app.add_routes([
    web.get('/', trigger_manager),
    web.post('/set_trigger', trigger_manager)
])

def task(watch_dog_queue_in):
    global watch_dog_queue
    watch_dog_queue = watch_dog_queue_in
    web.run_app(app, port=8082)
     
def start_timers_http(watch_dog_queue):
    p = multiprocessing.Process(target=task,  args=[watch_dog_queue])
    p.start()
    return p

if __name__ == "__main__":
    web.run_app(app, port=8082)
