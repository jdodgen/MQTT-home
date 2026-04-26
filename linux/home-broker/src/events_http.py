# MIT licence copyright 2026 jim dodgen
# built with the assistence of Google Gemini
# hard to get Gemini to do the tweeks  it gets lost.
# eventualy you need to make some mods
#
import asyncio
import aiohttp
from aiohttp import web
import aiohttp_jinja2
import jinja2
import aiosqlite
import http_common as config

DB_NAME =   config.DB_NAME
OUR_PORT =  config.EVENTS_PORT
NAV =       config.nav_section() # boot static, fork safe
STYLE =     config.STYLE
#
# --- EVENT HANDLERS ---
#
@aiohttp_jinja2.template('events.html')
async def handle_list_events(request):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT * FROM events") as cursor:
            rows = await cursor.fetchall()
            return {
            'events': rows,
            'query': request.query,
            "style": STYLE,
            }|NAV

async def handle_add_event(request):
    data = await request.post()
    
    # Convert 'true'/'false' strings from form to integers for SQLite
    on_change = 1 if data.get('only_on_change_of_payload') == 'true' else 0

    async with aiosqlite.connect(DB_NAME) as db:
        try:
            await db.execute("""
                INSERT INTO events (events_name, mqtt_topic, matching_payload, 
                                   only_on_change_of_payload, subject, body) 
                VALUES (?, ?, ?, ?, ?, ?)""",
                (data['events_name'], data['mqtt_topic'], data['matching_payload'], 
                 on_change, data['subject'], data['body'])
            )
            await db.commit()
        except aiosqlite.IntegrityError:
            return web.Response(text="Error: Event name already exists", status=400)
    
    raise web.HTTPFound('/events')

async def handle_delete_event(request):
    data = await request.post()
    name = data.get('events_name')

    async with aiosqlite.connect(DB_NAME) as db:
        # Fetch data to refill before it's gone
        async with db.execute("SELECT * FROM events WHERE events_name=?", (name,)) as cursor:
            row = await cursor.fetchone()
            
        await db.execute("DELETE FROM events WHERE events_name = ?", (name,))
        await db.commit()

    if row:
        # Redirect back with query params to pre-fill the form
        return web.HTTPFound(
            f'/events?refill_name={row[0]}&refill_topic={row[1]}&refill_payload={row[2]}'
            f'&refill_subj={row[4]}&refill_body={row[5]}'
        )
    return web.HTTPFound('/events')

# async def handle_test_http(request):
    # """Triggers an external HTTP request from the server side"""
    # test_url = "http://httpbin.org"
    
    # # Use ClientSession for asynchronous outbound calls
    # async with aiohttp.ClientSession() as session:
        # async with session.get(test_url) as resp:
            # status = resp.status
            # text = await resp.text()
            # print(f"External call to {test_url} returned {status}")
            
    # # Return a response or redirect back to the dashboard
    # return web.Response(text=f"HTTP Request to {test_url} succeeded with status {status}")
    
async def handle_run_event(request):
    data = await request.post()
    e_name = data.get('events_name')
    
    # Optional: Look up the event details from the DB using e_name
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT mqtt_topic, subject FROM events WHERE events_name = ?", (e_name,)) as cursor:
            row = await cursor.fetchone()
            if row:
                topic, subject = row
                print(f"Running action for {e_name} (Topic: {topic})")
                
                # Perform your external HTTP call here
                async with aiohttp.ClientSession() as session:
                    # Example: Sending the event name to an external service
                    async with session.post("http://httpbin.org", json={"event": e_name, "subj": subject}) as resp:
                        print(f"External call status: {resp.status}")

    # Redirect back so the user doesn't leave the page
    raise web.HTTPFound('/events')

@aiohttp_jinja2.template('manage_event.html')
async def handle_manage_view(request):
    event_name = request.query.get('events_name')
    async with aiosqlite.connect(DB_NAME) as db:
        # 1. Get all available options
        async with db.execute("SELECT camera_name FROM cameras") as c:
            all_cameras = [r[0] for r in await c.fetchall()]
        async with db.execute("SELECT emailaddr_name FROM emailaddr") as e:
            all_emails = [r[0] for r in await e.fetchall()]
        # 2. Get currently linked options
        async with db.execute("SELECT camera_name FROM cameras_in_events WHERE events_name=?", (event_name,)) as c:
            linked_cameras = [r[0] for r in await c.fetchall()]
        async with db.execute("SELECT emailaddr_name FROM emailaddr_in_events WHERE events_name=?", (event_name,)) as e:
            linked_emails = [r[0] for r in await e.fetchall()]

    return {
        'event_name':       event_name,
        'all_cameras':      all_cameras,
        'all_emails':       all_emails,
        'linked_cameras':   linked_cameras,
        'linked_emails':    linked_emails,
        "style":STYLE
    } | NAV

async def handle_update_links(request):
    data = await request.post()
    event_name = data.get('events_name')
    # getall returns multiple values for the same key (checkboxes)
    selected_cameras = data.getall('cameras', [])
    selected_emails =  data.getall('emails', [])
    async with aiosqlite.connect(DB_NAME) as db:
        # Clear existing links for this event
        await db.execute("DELETE FROM cameras_in_events WHERE events_name=?", (event_name,))
        await db.execute("DELETE FROM emailaddr_in_events WHERE events_name=?", (event_name,))
        # Insert new links
        for c in selected_cameras:
            await db.execute("INSERT INTO cameras_in_events VALUES (?, ?)", (event_name, c))
        for e in selected_emails:
            await db.execute("INSERT INTO emailaddr_in_events VALUES (?, ?)", (event_name, e))
        await db.commit()
    raise web.HTTPFound('/events')


# here we go !
# Store the IP once when the app starts

    
app = web.Application()

# 2. Setup Jinja2 (Tells 'app' where your HTML files are)
aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('./templates'))

# 3. Define your routes (Tells 'app' which URL runs which function)
app.add_routes([
    web.get('/',          handle_list_events),
    web.get('/events',          handle_list_events),
    web.post('/events/add',     handle_add_event),
    web.post('/events/delete',  handle_delete_event),
    #web.post('/test-http',      handle_test_http)
    web.get('/manage',          handle_manage_view),
    web.post('/update-links',   handle_update_links),
    web.post('/run-event',      handle_run_event)
])

# 4. Start the server
if __name__ == '__main__':
    web.run_app(app, port=8080)
