  # simple_emailer_http.py
import aiosqlite

async def get_configs(db_path):
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        
        # Execute query and fetch all results
        async with db.execute("SELECT * FROM config") as cursor:
            rows = await cursor.fetchall()
            
        return rows
