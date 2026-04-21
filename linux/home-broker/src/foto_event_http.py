# --- EMAIL HANDLERS --
import asyncio
from aiohttp import web
import aiohttp_jinja2
import jinja2
import aiosqlite

DB_NAME = "devices.db"
# --- EVENT HANDLERS ---

@aiohttp_jinja2.template('events.html')
async def handle_list_events(request):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT * FROM events") as cursor:
            rows = await cursor.fetchall()
            return {'events': rows}

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
        await db.execute("DELETE FROM events WHERE events_name = ?", (name,))
        await db.commit()
    
    raise web.HTTPFound('/events')
    
import aiohttp # Ensure this is imported

async def handle_test_http(request):
    """Triggers an external HTTP request from the server side"""
    test_url = "http://httpbin.org"
    
    # Use ClientSession for asynchronous outbound calls
    async with aiohttp.ClientSession() as session:
        async with session.get(test_url) as resp:
            status = resp.status
            text = await resp.text()
            print(f"External call to {test_url} returned {status}")
            
    # Return a response or redirect back to the dashboard
    return web.Response(text=f"HTTP Request to {test_url} succeeded with status {status}")

    
app = web.Application()

# 2. Setup Jinja2 (Tells 'app' where your HTML files are)
aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('./templates'))

# 3. Define your routes (Tells 'app' which URL runs which function)
app.add_routes([
    web.get('/events', handle_list_events),
    web.post('/events/add', handle_add_event),
    web.post('/events/delete', handle_delete_event),
    web.post('/test-http', handle_test_http)
])

# 4. Start the server
if __name__ == '__main__':
    web.run_app(app, port=8080)
