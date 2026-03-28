import sqlite3
import psycopg2
import os
from dotenv import load_dotenv

# Загружаем переменные
load_dotenv()

SQLITE_PATH = 'merged_bot/biblia/simple_bible_bot.db'
POSTGRES_URL = os.getenv('BIBLIA_DATABASE_URL') or os.getenv('DATABASE_URL')

def migrate():
    if not POSTGRES_URL:
        print("❌ Ошибка: DATABASE_URL не установлена!")
        return

    print("🚀 Начинаем миграцию из SQLite в PostgreSQL...")

    try:
        # Подключаемся к SQLite
        sqlite_conn = sqlite3.connect(SQLITE_PATH)
        sqlite_cursor = sqlite_conn.cursor()

        # Подключаемся к PostgreSQL
        pg_conn = psycopg2.connect(POSTGRES_URL)
        pg_cursor = pg_conn.cursor()

        # 1. Создаем таблицы в Postgres, если их нет
        pg_cursor.execute('''
            CREATE TABLE IF NOT EXISTS biblia_chats (
                chat_id BIGINT PRIMARY KEY,
                chat_title TEXT NOT NULL,
                is_enabled BOOLEAN DEFAULT TRUE,
                added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        pg_cursor.execute('''
            CREATE TABLE IF NOT EXISTS biblia_quotes (
                id SERIAL PRIMARY KEY,
                text TEXT NOT NULL,
                book TEXT NOT NULL,
                chapter INTEGER,
                verse TEXT,
                used_count INTEGER DEFAULT 0,
                added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        pg_conn.commit()

        # 2. Мигрируем чаты
        sqlite_cursor.execute("SELECT chat_id, chat_title FROM chats")
        chats = sqlite_cursor.fetchall()
        print(f"📦 Найдено чатов в SQLite: {len(chats)}")
        
        for chat in chats:
            pg_cursor.execute(
                "INSERT INTO biblia_chats (chat_id, chat_title) VALUES (%s, %s) ON CONFLICT (chat_id) DO NOTHING",
                chat
            )
        
        # 3. Мигрируем цитаты
        sqlite_cursor.execute("SELECT text, book, chapter, verse FROM quotes")
        quotes = sqlite_cursor.fetchall()
        print(f"📦 Найдено цитат в SQLite: {len(quotes)}")
        
        for quote in quotes:
            pg_cursor.execute(
                "INSERT INTO biblia_quotes (text, book, chapter, verse) VALUES (%s, %s, %s, %s)",
                quote
            )

        pg_conn.commit()
        print("✅ Миграция завершена успешно!")

    except Exception as e:
        print(f"❌ Ошибка во время миграции: {e}")
    finally:
        sqlite_conn.close()
        pg_conn.close()

if __name__ == "__main__":
    migrate()
