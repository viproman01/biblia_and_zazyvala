import asyncio
import aiosqlite
import asyncpg
import os
from dotenv import load_dotenv

async def migrate_zazyvala():
    load_dotenv()
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL not found!")
        return

    print("Подключение к PostgreSQL...")
    pg_conn = await asyncpg.connect(db_url)
    
    print("Подключение к SQLite (bot_data.db)...")
    async with aiosqlite.connect("bot_data.db") as sqlite_conn:
        
        # 1. Миграция members
        cursor = await sqlite_conn.execute("SELECT user_id, chat_id, username, first_name, last_name, last_seen, is_active FROM members")
        members = await cursor.fetchall()
        print(f"Найдено {len(members)} участников в SQLite.")
        
        inserted = 0
        for m in members:
            try:
                await pg_conn.execute("""
                    INSERT INTO members (user_id, chat_id, username, first_name, last_name, last_seen, is_active)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    ON CONFLICT(user_id, chat_id) DO NOTHING
                """, m[0], m[1], m[2], m[3], m[4], m[5], m[6])
                inserted += 1
            except Exception as e:
                pass
        print(f"Добавлено {inserted} новых участников в Postgres.")

        # 2. Миграция message_stats (опционально, но полезно)
        cursor = await sqlite_conn.execute("SELECT message_type, sent_at, chat_id FROM message_stats")
        stats = await cursor.fetchall()
        print(f"Найдено {len(stats)} логов статистики в SQLite.")
        
        inserted_stats = 0
        for s in stats:
            try:
                await pg_conn.execute("""
                    INSERT INTO message_stats (message_type, sent_at, chat_id)
                    VALUES ($1, $2, $3)
                """, s[0], s[1], s[2])
                inserted_stats += 1
            except Exception as e:
                pass
        print(f"Добавлено {inserted_stats} логов статистики в Postgres.")

    await pg_conn.close()
    print("✅ Миграция Зазывалы завершена!")

if __name__ == "__main__":
    asyncio.run(migrate_zazyvala())
