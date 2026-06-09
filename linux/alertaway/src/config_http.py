import asyncio
from aiohttp import web
import aiohttp_jinja2
import jinja2
import aiosqlite
import http_common as config


async def get_config(db_path):
    # 'async with' handles opening and automatically closing the connection
    async with aiosqlite.connect(db_path) as db:
        # Set the row_factory to return Row objects (for column-name access)
        db.row_factory = aiosqlite.Row
        # 'execute' is an async method; use 'async with' to handle the cursor
        async with db.execute("SELECT * FROM config WHERE id = 0") as cursor:
            # 'fetchone' is also a coroutine and must be awaited
            row = await cursor.fetchone()
        return row

async def update_config(db_path, data):
    # 'async with' ensures the connection is closed even if an error occurs
    async with aiosqlite.connect(db_path) as db:
        # Business logic remains the same
        ssl_val = 1 if 'ssl' in data else 0
        
        sql = """UPDATE config SET 
                    alive_interval = ?, 
                    publish = ?,
                    -- local broker mosquitto
                    local_broker_ip = ?,
                    local_broker_port = ?,
                    local_broker_ssl = ?,
                    local_broker_user = ?,
                    local_broker_password = ?,
                    local_broker_sleep_seconds = ?,
                    local_broker_mqtt_keepalive = ?,
                    -- cloud broker (optional)
                    cloud_broker_ip = ?,
                    cloud_broker_port = ?,
                    cloud_broker_ssl = ?,
                    cloud_broker_user = ?,
                    cloud_broker_password = ?,
                    cloud_broker_sleep_seconds = ?,
                    cloud_broker_mqtt_keepalive = ?,
                    --- 
                    gmail_password = ?,
                    gmail_user =?
                 WHERE id = 0"""
        # In aiosqlite, .execute() and .commit() must be awaited
        await db.execute(sql, (
                                data['alive_interval'], 
                                data['publish'],
                                #data['zigbee_refresh_seconds'],
                                # local broker mosquitto
                                data['local_broker_ip'],
                                data['local_broker_port'],
                                data.get('local_broker_ssl', '0'),
                                data['local_broker_user'],
                                data['local_broker_password'],
                                data['local_broker_sleep_seconds'],
                                data['local_broker_mqtt_keepalive'],
                                #-- cloud broker (optional)
                                data['cloud_broker_ip'],
                                data['cloud_broker_port'],
                                data.get('cloud_broker_ssl', '0'),
                                data['cloud_broker_user'],
                                data['cloud_broker_password'],
                                data['cloud_broker_sleep_seconds'],
                                data['cloud_broker_mqtt_keepalive'],
                                #
                                data['gmail_password'],
                                data['gmail_user']
        ))
        await db.commit()


# --- Handlers ---
@aiohttp_jinja2.template("config.html")
async def handle_index(request):
    config_row = await get_config(request.app['db_path'])
    return {"config": config_row, "style": config.STYLE} | config.nav_section()

async def handle_update(request):
    # Retrieve form data from POST
    data = await request.post()
    # print(data)
    await update_config(request.app['db_path'], data)
    # Redirect back to home after update
    return web.HTTPFound('/')

# --- App Setup ---
async def init_app():
    app = web.Application()
    app['db_path'] = 'devices.db'
    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader("templates"))
    
    app.add_routes([
        web.get('/', handle_index),
        web.post('/update', handle_update) # New POST route
    ])
    return app

def main():
    web.run_app(init_app(), port=config.CONFIG_PORT)

def start_daemon():
    p = multiprocessing.Process(target=main)
    p.start()
    return p

if __name__ == "__main__":
    main()
