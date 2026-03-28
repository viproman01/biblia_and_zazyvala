import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
url = os.getenv('BIBLIA_DATABASE_URL') or os.getenv('DATABASE_URL')

try:
    conn = psycopg2.connect(url)
    cursor = conn.cursor()
    cursor.execute("ALTER TABLE biblia_quotes ADD COLUMN IF NOT EXISTS used_count INTEGER DEFAULT 0")
    conn.commit()
    print("✅ Колонка used_count успешно добавлена (или уже существовала)!")
    conn.close()
except Exception as e:
    print(f"Ошибка: {e}")
