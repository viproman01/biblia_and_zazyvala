import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
url = os.getenv('BIBLIA_DATABASE_URL') or os.getenv('DATABASE_URL')

try:
    conn = psycopg2.connect(url)
    cursor = conn.cursor()
    cursor.execute("ALTER TABLE biblia_chats ADD COLUMN IF NOT EXISTS is_enabled BOOLEAN DEFAULT TRUE")
    cursor.execute("ALTER TABLE biblia_chats ADD COLUMN IF NOT EXISTS added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
    conn.commit()
    print("✅ Схема biblia_chats успешно обновлена!")
    conn.close()
except Exception as e:
    print(f"Ошибка: {e}")
