# --- EMAIL HANDLERS --
import asyncio
from aiohttp import web
import aiohttp_jinja2
import jinja2
import aiosqlite
import http_common

DB_NAME =   http_common.DB_NAME
OUR_PORT =  http_common.EMAIL_PORT
http_vars = http_common.http_vars()

@aiohttp_jinja2.template('emailaddr.html')
async def handle_list_emails(request):
    """Fetch and display all email records"""
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT emailaddr_name, email_address FROM emailaddr") as cursor:
            rows = await cursor.fetchall()
            return {'emails': rows}|http_vars

async def handle_add_email(request):
    """Add a new name and email address"""
    data = await request.post()
    name = data.get('emailaddr_name')
    address = data.get('email_address')

    async with aiosqlite.connect(DB_NAME) as db:
        try:
            await db.execute(
                "INSERT INTO emailaddr (emailaddr_name, email_address) VALUES (?, ?)",
                (name, address)
            )
            await db.commit()
        except aiosqlite.IntegrityError:
            return web.Response(text="Error: Name already exists", status=400)
    
    raise web.HTTPFound('/emails')

async def handle_delete_email(request):
    """Delete an email record using the primary key (name)"""
    data = await request.post()
    name = data.get('emailaddr_name')

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM emailaddr WHERE emailaddr_name = ?", (name,))
        await db.commit()
    
    raise web.HTTPFound('/emails')

# --- ROUTES ---
app = web.Application()
aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('./templates'))

app.add_routes([
    web.get('/', handle_list_emails),
    web.get('/emails', handle_list_emails),
    web.post('/emails/add', handle_add_email),
    web.post('/emails/delete', handle_delete_email)
])

if __name__ == '__main__':
    web.run_app(app, port=OUR_PORT)

