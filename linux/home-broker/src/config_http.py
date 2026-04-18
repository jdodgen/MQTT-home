import asyncio
from aiohttp import web
import aiohttp_jinja2
import jinja2
import aiosqlite

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
                 broker = ?, 
                 ssl = ?,
                 user = ?,
                 password = ?,
                 gmail_user = ?,
                 gmail_password = ?,
                 publish = ? 
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
            data['publish']
        ))
        await db.commit()


# --- Handlers ---
@aiohttp_jinja2.template("config.html")
async def handle_index(request):
    config_row = await get_config(request.app['db_path'])
    return {"config": config_row}

async def handle_update(request):
    # Retrieve form data from POST
    data = await request.post()
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

if __name__ == "__main__":
    web.run_app(init_app(), port=8082)
