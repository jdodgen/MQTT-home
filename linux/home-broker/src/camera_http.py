import asyncio
from aiohttp import web, ClientSession
import aiohttp_jinja2
import jinja2
import aiosqlite
import http_common as config

DB_NAME =   config.DB_NAME
OUR_PORT =  config.CAM_PORT

# --- HANDLERS ---

@aiohttp_jinja2.template('cameras.html')
async def handle_list(request):
    async with aiosqlite.connect(DB_NAME) as db:
        # This allows you to use camera['url'] or camera['camera_name'] in Jinja
        db.row_factory = aiosqlite.Row 
        async with db.execute("SELECT * FROM cameras order by camera_name") as cursor:
            rows = await cursor.fetchall()
            return {'cameras': rows, 'edit_data': request.query, "style": config.STYLE} | config.nav_section()

async def handle_edit_redirect(request):
    """Fetches data and redirects to form WITHOUT deleting from DB"""
    c_name = request.query.get('camera_name')
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT * FROM cameras WHERE camera_name = ?", (c_name,)) as cursor:
            row = await cursor.fetchone()
            if row:
                # Redirect to home with data to pre-fill
                return web.HTTPFound(f"/?camera_name={row[0]}&url={row[1]}&user={row[2]}&password={row[3]}&rotate={row[4]}")
    raise web.HTTPFound('/')

async def handle_delete(request):
    """Deletes the camera, but still sends the data to the form as a 'last look'"""
    data = await request.post()
    c_name = data.get('camera_name')
    async with aiosqlite.connect(DB_NAME) as db:
        # Get data before we kill the record
        async with db.execute("SELECT * FROM cameras WHERE camera_name = ?", (c_name,)) as cursor:
            row = await cursor.fetchone()
            await db.execute("DELETE FROM cameras WHERE camera_name = ?", (c_name,))
            await db.execute("DELETE FROM cameras_in_events WHERE camera_name = ?", (c_name,))
            await db.commit()
            if row:
                return web.HTTPFound(f"/?camera_name={row[0]}&url={row[1]}&user={row[2]}&password={row[3]}&rotate={row[4]}")
    raise web.HTTPFound('/')

# --- APP SETUP ---

async def handle_add(request):
    data = await request.post()
    async with aiosqlite.connect(DB_NAME) as db:
        # Use REPLACE INTO to handle 'Edit' (which is just an overwrite)
        await db.execute(
            "INSERT OR REPLACE INTO cameras (camera_name, url, user, password, rotate) VALUES (?, ?, ?, ?, ?)",
            (data['camera_name'], data['url'], data['user'], data['password'], data['rotate'])
        )
        await db.commit()
    raise web.HTTPFound('/')

async def handle_edit_load(request):
    """Instead of deleting, we fetch data and redirect to UI with params"""
    data = await request.post()
    c_name = data.get('camera_name')
    
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT * FROM cameras WHERE camera_name = ?", (c_name,)) as cursor:
            row = await cursor.fetchone()
            if row:
                # Delete from DB then send to form
                await db.execute("DELETE FROM cameras WHERE camera_name = ?", (c_name,))
                await db.commit()
                # Redirect back to home with the data in the URL
                return web.HTTPFound(f"/?camera_name={row[0]}&url={row[1]}&user={row[2]}&password={row[3]}&rotate={row[4]}")
    
    raise web.HTTPFound('/')

from aiohttp import web, ClientSession, DigestAuthMiddleware

async def handle_test_jpg(request):
    url = request.query.get('url')
    user = request.query.get('user', '')
    password = request.query.get('password', '')

    if not url:
        return web.Response(text="No URL provided", status=400)

    try:
        # Create middleware for Digest Authentication
        auth_middleware = DigestAuthMiddleware(login=user, password=password)
        
        # Pass the middleware to the ClientSession
        async with ClientSession(middlewares=[auth_middleware]) as session:
            async with session.get(url, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    return web.Response(body=data, content_type='image/jpeg')
                else:
                    # If it's still 401, the username/password is likely wrong
                    return web.Response(text=f"Auth Failed ({resp.status})", status=resp.status)
    except Exception as e:
        return web.Response(text=f"Connection Error: {str(e)}", status=500)

def run():
    # --- APP SETUP ---
    app = web.Application()
    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('./templates'))

    app.add_routes([
        web.get('/', handle_list),
        web.post('/add', handle_add),         # Uses INSERT OR REPLACE
        web.get('/edit', handle_edit_redirect), # New helper route
        web.post('/delete', handle_delete),
        web.get('/test', handle_test_jpg)
    ])
    web.run_app(app, port=OUR_PORT)

if __name__ == '__main__':
    run()
