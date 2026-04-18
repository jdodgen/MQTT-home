  # simple_emailer_http.py
import aiosqlite

async def get_configs(db_path):
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        # Execute query and fetch all results
        async with db.execute("SELECT * FROM config") as cursor:
            rows = await cursor.fetchall()
        return rows

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
