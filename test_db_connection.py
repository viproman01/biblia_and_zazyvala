import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# Проверяем оба варианта URL
urls = {
    'BIBLIA_DATABASE_URL': os.getenv('BIBLIA_DATABASE_URL'),
    'DATABASE_URL': os.getenv('DATABASE_URL')
}

print("Эмуляция подключения как на Render...")

for name, url in urls.items():
    print(f"\n--- Проверка {name} ---")
    if not url:
        print("❌ Переменная не задана в локальном .env")
        continue
        
    try:
        conn = psycopg2.connect(url)
        cursor = conn.cursor()
        
        # Проверяем таблицы Библии
        cursor.execute("SELECT to_regclass('public.biblia_quotes')")
        table_exists = cursor.fetchone()[0]
        
        if table_exists:
            cursor.execute("SELECT count(*) FROM biblia_quotes")
            count = cursor.fetchone()[0]
            print(f"✅ Таблица biblia_quotes НАЙДЕНА. Количество цитат: {count}")
        else:
            print("❌ Таблица biblia_quotes НЕ СУЩЕСТВУЕТ в этой базе данных.")
            
        conn.close()
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
