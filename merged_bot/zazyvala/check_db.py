import asyncio
import aiosqlite

async def check_db():
    async with aiosqlite.connect("bot_data.db") as db:
        async with db.execute("SELECT * FROM members") as cursor:
            rows = await cursor.fetchall()
            print(f"Members: {rows}")
        async with db.execute("SELECT * FROM message_stats") as cursor:
            rows = await cursor.fetchall()
            print(f"Stats: {rows}")

if __name__ == "__main__":
    asyncio.run(check_db())
