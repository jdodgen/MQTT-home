import asyncio
from aiohttp import web
import aiohttp_jinja2
import jinja2
import aiosqlite
import http_common as config


OUR_PORT =  config.CONFIG_PORT
DB_NAME =   config.DB_NAME
OUR_PORT =  config.TRIGGERS_PORT
NAV =       config.nav_section()
STYLE = 	config.STYLE

async def get_config():
    # 'async with' handles opening and automatically closing the connection
    async with aiosqlite.connect(DB_NAME) as db:
        # Set the row_factory to return Row objects (for column-name access)
        db.row_factory = aiosqlite.Row
        # 'execute' is an async method; use 'async with' to handle the cursor
        async with db.execute("SELECT * FROM config WHERE id = 0") as cursor:
            # 'fetchone' is also a coroutine and must be awaited
            row = await cursor.fetchone()
        return row

async def update_config(data):
    # 'async with' ensures the connection is closed even if an error occurs
    async with aiosqlite.connect(DB_NAME) as db:
        # Business logic remains the same
        ssl_val = 1 if 'ssl' in data else 0
        
        sql = """UPDATE config SET 
                 alive_interval = ?, 
                 broker = ?, 
                 ssl = ?,
                 user = ?,
                 password = ?,
                 gmail_user = ?,
                 gmail_password = ?,
                 publish = ?,
                 zigbee_refresh_seconds = ?,
                 mosquitto_sleep_seconds = ?,
                 broker_mqtt_port = ?
                 WHERE id = 0"""
        # In aiosqlite, .execute() and .commit() must be awaited
        await db.execute(sql, (
            int(data['alive_interval']),
            data['broker'],
            ssl_val,
            data['user'],
            data['password'],
            data['gmail_user'],
            data['gmail_password'],
            data['alive_publish_topic'],
            data['zigbee_refresh_seconds'],
            data['mosquitto_sleep_seconds'],
            data['broker_mqtt_port'],
        ))
        await db.commit()


# --- Handlers ---
@aiohttp_jinja2.template("config.html")
async def handle_index(request):
    config_row = await get_config()
    return {"config": config_row, "style": STYLE,} | NAV

async def handle_update(request):
    # Retrieve form data from POST
    data = await request.post()
    await update_config(data)
    # Redirect back to home after update
    return web.HTTPFound('/')

# --- App Setup ---
# Store the IP once when the app starts
MY_IP = config.get_ip()
    
app = web.Application()

# 2. Setup Jinja2 (Tells 'app' where your HTML files are)
aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('./templates'))

# 3. Define your routes (Tells 'app' which URL runs which function)
app.add_routes([
    web.get('/', handle_index),
    web.post('/update', handle_update) # New POST route
])

# 4. Start the server
if __name__ == '__main__':
    web.run_app(app, port=OUR_PORT)

