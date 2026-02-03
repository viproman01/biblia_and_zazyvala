import aiosqlite
import asyncpg
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DATABASE_PATH = "bot_data.db"
DATABASE_URL = os.getenv("DATABASE_URL")

async def get_db():
    if DATABASE_URL:
        # PostgreSQL connection
        return await asyncpg.connect(DATABASE_URL)
    else:
        # SQLite connection
        return await aiosqlite.connect(DATABASE_PATH)

async def init_db():
    """Инициализация базы данных"""
    if DATABASE_URL:
        conn = await get_db()
        try:
            # Таблица участников
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS members (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    chat_id BIGINT NOT NULL,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    last_seen TEXT,
                    is_active INTEGER DEFAULT 1,
                    UNIQUE(user_id, chat_id)
                )
            """)
            
            # Индекс
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_members_chat 
                ON members(chat_id, is_active)
            """)
            
            # Таблица статистики
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS message_stats (
                    id SERIAL PRIMARY KEY,
                    message_type TEXT,
                    sent_at TEXT,
                    chat_id BIGINT
                )
            """)
        finally:
            await conn.close()
    else:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS members (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    chat_id INTEGER NOT NULL,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    last_seen TEXT,
                    is_active INTEGER DEFAULT 1,
                    UNIQUE(user_id, chat_id)
                )
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_members_chat 
                ON members(chat_id, is_active)
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS message_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_type TEXT,
                    sent_at TEXT,
                    chat_id INTEGER
                )
            """)
            await db.commit()

async def add_member(user_id: int, username: str, first_name: str, last_name: str, chat_id: int):
    """Добавить или обновить участника"""
    now = datetime.now().isoformat()
    if DATABASE_URL:
        conn = await get_db()
        try:
            await conn.execute("""
                INSERT INTO members (user_id, chat_id, username, first_name, last_name, last_seen, is_active)
                VALUES ($1, $2, $3, $4, $5, $6, 1)
                ON CONFLICT(user_id, chat_id) DO UPDATE SET
                    username = EXCLUDED.username,
                    first_name = EXCLUDED.first_name,
                    last_name = EXCLUDED.last_name,
                    last_seen = EXCLUDED.last_seen,
                    is_active = 1
            """, user_id, chat_id, username, first_name, last_name, now)
        finally:
            await conn.close()
    else:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute("""
                INSERT INTO members (user_id, chat_id, username, first_name, last_name, last_seen, is_active)
                VALUES (?, ?, ?, ?, ?, ?, 1)
                ON CONFLICT(user_id, chat_id) DO UPDATE SET
                    username = excluded.username,
                    first_name = excluded.first_name,
                    last_name = excluded.last_name,
                    last_seen = excluded.last_seen,
                    is_active = 1
            """, (user_id, chat_id, username, first_name, last_name, now))
            await db.commit()

async def remove_member(user_id: int, chat_id: int):
    """Отметить как неактивного"""
    if DATABASE_URL:
        conn = await get_db()
        try:
            await conn.execute("UPDATE members SET is_active = 0 WHERE user_id = $1 AND chat_id = $2", user_id, chat_id)
        finally:
            await conn.close()
    else:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute("UPDATE members SET is_active = 0 WHERE user_id = ? AND chat_id = ?", (user_id, chat_id))
            await db.commit()

async def get_chat_members(chat_id: int):
    """Получить активных участников"""
    if DATABASE_URL:
        conn = await get_db()
        try:
            rows = await conn.fetch("""
                SELECT user_id, username, first_name, last_name
                FROM members 
                WHERE chat_id = $1 AND is_active = 1
                ORDER BY last_seen DESC
            """, chat_id)
            return rows
        finally:
            await conn.close()
    else:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            cursor = await db.execute("""
                SELECT user_id, username, first_name, last_name
                FROM members 
                WHERE chat_id = ? AND is_active = 1
                ORDER BY last_seen DESC
            """, (chat_id,))
            return await cursor.fetchall()

async def get_member_count(chat_id: int = None):
    """Количество участников"""
    if DATABASE_URL:
        conn = await get_db()
        try:
            if chat_id:
                val = await conn.fetchval("SELECT COUNT(*) FROM members WHERE chat_id = $1 AND is_active = 1", chat_id)
            else:
                val = await conn.fetchval("SELECT COUNT(DISTINCT user_id) FROM members WHERE is_active = 1")
            return val or 0
        finally:
            await conn.close()
    else:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            if chat_id:
                cursor = await db.execute("SELECT COUNT(*) FROM members WHERE chat_id = ? AND is_active = 1", (chat_id,))
            else:
                cursor = await db.execute("SELECT COUNT(DISTINCT user_id) FROM members WHERE is_active = 1")
            result = await cursor.fetchone()
            return result[0] if result else 0

async def log_message(message_type: str, chat_id: int):
    """Лог сообщения"""
    now = datetime.now().isoformat()
    if DATABASE_URL:
        conn = await get_db()
        try:
            await conn.execute("INSERT INTO message_stats (message_type, sent_at, chat_id) VALUES ($1, $2, $3)", message_type, now, chat_id)
        finally:
            await conn.close()
    else:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute("INSERT INTO message_stats (message_type, sent_at, chat_id) VALUES (?, ?, ?)", (message_type, now, chat_id))
            await db.commit()

async def get_stats(chat_id: int = None):
    """Статистика"""
    if DATABASE_URL:
        conn = await get_db()
        try:
            if chat_id:
                total = await conn.fetchval("SELECT COUNT(*) FROM message_stats WHERE chat_id = $1", chat_id)
                calls = await conn.fetchval("SELECT COUNT(*) FROM message_stats WHERE message_type = 'call' AND chat_id = $1", chat_id)
            else:
                total = await conn.fetchval("SELECT COUNT(*) FROM message_stats")
                calls = await conn.fetchval("SELECT COUNT(*) FROM message_stats WHERE message_type = 'call'")
            
            member_count = await get_member_count(chat_id)
            return {"total_messages": total or 0, "call_count": calls or 0, "member_count": member_count}
        finally:
            await conn.close()
    else:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            if chat_id:
                cursor = await db.execute("SELECT COUNT(*) FROM message_stats WHERE chat_id = ?", (chat_id,))
                total = (await cursor.fetchone())[0]
                cursor = await db.execute("SELECT COUNT(*) FROM message_stats WHERE message_type = 'call' AND chat_id = ?", (chat_id,))
                calls = (await cursor.fetchone())[0]
            else:
                cursor = await db.execute("SELECT COUNT(*) FROM message_stats")
                total = (await cursor.fetchone())[0]
                cursor = await db.execute("SELECT COUNT(*) FROM message_stats WHERE message_type = 'call'")
                calls = (await cursor.fetchone())[0]
            
            member_count = await get_member_count(chat_id)
            return {"total_messages": total, "call_count": calls, "member_count": member_count}

