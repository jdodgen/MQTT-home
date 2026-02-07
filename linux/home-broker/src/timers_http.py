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
async def timer_manager(request):
    db = request.app['db']
    context = {
        "timers_here": "here",
        "timer_msg": "",
        "time_now": datetime.now().strftime("%H:%M"),
        "debug": ""
    }

    # 1. Handle Form Actions (POST)
    if request.method == "POST":
        form = await request.post()
        print("form\n", form)
        state = form.get("state", "")
        print("state [%s]" % (state,))
        # Logic for "Set timer"
        if state == "Set timer":
            selected_rowid = form.get("selected_rowid")
            days_list = form.getall("TIMED:days", [])
            days_str = ",".join(days_list)
            print("processing new timer\ndays_list[%s] rowid[%s]" % (days_str, selected_rowid))
            
            if selected_rowid and days_str:
                # Setup time logic
                is_start_fixed = form.get("TIMED:start") == "Fixed"
                is_stop_fixed = form.get("TIMED:stop") == "Fixed"
                (topic, true_value, false_value) = db.get_device_info(selected_rowid)
                print("[%s][%s]{%s]" % (topic, true_value, false_value))
                
                db.con.execute("""
                    INSERT INTO timers (
                        topic, true_value, false_value, days, start_type, stop_type, 
                        start_hour, start_minute, start_offset, 
                        stop_hour, stop_minute, stop_offset, state
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    topic, 
                    true_value, 
                    false_value, 
                    days_str, 
                    form.get("TIMED:start"), 
                    form.get("TIMED:stop"),
                    form.get("TIMED:starthour") if is_start_fixed else 0,
                    form.get("TIMED:startminute") if is_start_fixed else 0,
                    form.get("TIMED:startoffset") if not is_start_fixed else 0,
                    form.get("TIMED:stophour") if is_stop_fixed else 0,
                    form.get("TIMED:stopminute") if is_stop_fixed else 0,
                    form.get("TIMED:stopoffset") if not is_stop_fixed else 0,
                    form.get("TIMED:state")
                ))
                db.con.commit()
            else:
                context["timer_msg"] = "ERROR:  no device checked or no days checked"

        # Logic for "Remove Timer"
        elif "Remove Timer:" in state:
            match = re.search(r'Remove Timer:(\d+)', state)
            if match:
                target_id = match.group(1)
                db.con.execute("DELETE FROM timers WHERE rowid = ?", (target_id,))
                db.con.commit()

    # 2. Fetch Data for the UI (Always happens for GET and after POST)
    # Fetch available alerts for the <select> box
    #cursor = db.execute("SELECT * FROM devices") # Adjust table name as needed
    context['alerts'] = db.get_timers_devices() # await cursor.fetchall()

    # Fetch existing timers for the bottom table
    # cursor = db.execute("SELECT rowid, * FROM timed_events")
    context['timed_alerts'] = db.get_all_timers() #cursor.fetchall()
    context["IPaddr"] = const.IPaddr

    return aiohttp_jinja2.render_template('timers.html', request, context)

# --- APP ROUTING ---
app = web.Application()
aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('./templates'))

app.on_startup.append(init_db)
app.on_cleanup.append(close_db)

app.add_routes([
    web.get('/', timer_manager),
    web.post('/set_timer', timer_manager)
])

def task():
    web.run_app(app, port=8081)
     
def start_timers_http():
    p = multiprocessing.Process(target=task)
    p.start()
    return p

if __name__ == "__main__":
    web.run_app(app, port=8081)
