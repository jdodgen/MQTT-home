import asyncio
from aiohttp import web
import aiohttp_jinja2
import jinja2
import aiosqlite
import http_common

DB_NAME =   http_common.DB_NAME
OUR_PORT =  http_common.CAM_PORT
http_vars = http_common.http_vars()


# --- HANDLERS ---

@aiohttp_jinja2.template('cameras.html')
async def handle_list(request):
    """Displays all cameras and the add/delete forms"""
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT * FROM cameras") as cursor:
            rows = await cursor.fetchall()
            return {'cameras': rows}|http_vars

async def handle_add(request):
    """Adds a new camera record"""
    data = await request.post()
    
    async with aiosqlite.connect(DB_NAME) as db:
        try:
            await db.execute(
                "INSERT INTO cameras (camera_name, url, user, password, rotate) VALUES (?, ?, ?, ?, ?)",
                (data['camera_name'], data['url'], data['user'], data['password'], data['rotate'])
            )
            await db.commit()
        except aiosqlite.IntegrityError:
            return web.Response(text="Error: Camera name already exists", status=400)
    
    raise web.HTTPFound('/')

async def handle_delete(request):
    """Deletes a camera by its primary key (camera_name)"""
    data = await request.post()
    c_name = data.get('camera_name')

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM cameras WHERE camera_name = ?", (c_name,))
        await db.commit()
    
    raise web.HTTPFound('/')

# --- APP SETUP ---

app = web.Application()
aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('./templates'))

app.add_routes([
    web.get('/', handle_list),
    web.post('/add', handle_add),
    web.post('/delete', handle_delete)
])

if __name__ == '__main__':
    web.run_app(app, port=8080)
