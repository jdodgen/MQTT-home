import re
import aiosqlite
import aiohttp_jinja2
import jinja2
from aiohttp import web

# --- DATABASE SETUP ---
async def init_db(app):
    # Open connection once at startup
    db = await aiosqlite.connect("automation.db")
    db.row_factory = aiosqlite.Row  # Access columns by name: row['desc']
    app['db'] = db

async def close_db(app):
    await app['db'].close()

# --- THE MAIN HANDLER ---
async def timer_manager(request):
    db = request.app['db']
    context = {
        "timers_here": "here",
        "timer_msg": "",
        "time_now": "14:30", # You can use datetime.now()
        "debug": ""
    }

    # 1. Handle Form Actions (POST)
    if request.method == "POST":
        form = await request.post()
        state = form.get("state", "")

        # Logic for "Set timer"
        if state == "Set timer":
            alert_val = form.get("TIMED:alert")
            days_list = form.getall("TIMED:days", [])
            
            if alert_val and days_list:
                # Mirroring your split /:/
                ah, al, port, logic, rowid = alert_val.split(':')
                days_str = ",".join(days_list)
                
                # Setup time logic
                is_start_fixed = form.get("TIMED:start") == "Fixed"
                is_stop_fixed = form.get("TIMED:stop") == "Fixed"

                await db.execute("""
                    INSERT INTO timed_events (
                        ah, al, port, days, start_type, stop_type, 
                        start_hour, start_minute, start_offset, 
                        stop_hour, stop_minute, stop_offset, state
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    ah, al, port, days_str, 
                    form.get("TIMED:start"), form.get("TIMED:stop"),
                    form.get("TIMED:starthour") if is_start_fixed else 0,
                    form.get("TIMED:startminute") if is_start_fixed else 0,
                    form.get("TIMED:startoffset") if not is_start_fixed else 0,
                    form.get("TIMED:stophour") if is_stop_fixed else 0,
                    form.get("TIMED:stopminute") if is_stop_fixed else 0,
                    form.get("TIMED:stopoffset") if not is_stop_fixed else 0,
                    form.get("TIMED:state")
                ))
                await db.commit()
            else:
                context["timer_msg"] = "Timed alert failed, missing device or days?"

        # Logic for "Remove Timer"
        elif "Remove Timer:" in state:
            match = re.search(r'Remove Timer:(\d+)', state)
            if match:
                target_id = match.group(1)
                await db.execute("DELETE FROM timed_events WHERE rowid = ?", (target_id,))
                await db.commit()

    # 2. Fetch Data for the UI (Always happens for GET and after POST)
    # Fetch available alerts for the <select> box
    cursor = await db.execute("SELECT * FROM devices") # Adjust table name as needed
    context['alerts'] = await cursor.fetchall()

    # Fetch existing timers for the bottom table
    cursor = await db.execute("SELECT rowid, * FROM timed_events")
    context['timed_alerts'] = await cursor.fetchall()

    return aiohttp_jinja2.render_template('timers.html', request, context)

# --- APP ROUTING ---
app = web.Application()
aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('./templates'))

app.on_startup.append(init_db)
app.on_cleanup.append(close_db)

app.add_routes([
    web.get('/timers', timer_manager),
    web.post('/timers', timer_manager)
])

if __name__ == "__main__":
    web.run_app(app, port=8080)
