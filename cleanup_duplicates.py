import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

url = os.getenv('BIBLIA_DATABASE_URL') or os.getenv('DATABASE_URL')

try:
    conn = psycopg2.connect(url)
    cursor = conn.cursor()
    
    # Считаем общее количество
    cursor.execute("SELECT count(*) FROM biblia_quotes")
    total = cursor.fetchone()[0]
    
    # Удаляем дубликаты (оставляем только одну запись с минимальным ID для каждого текста)
    cursor.execute("""
        DELETE FROM biblia_quotes
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM biblia_quotes
            GROUP BY text, book, chapter, verse
        )
    """)
    conn.commit()
    
    # Считаем после удаления
    cursor.execute("SELECT count(*) FROM biblia_quotes")
    remaining = cursor.fetchone()[0]
    
    print(f"Было цитат: {total}")
    print(f"Удалено дубликатов: {total - remaining}")
    print(f"Осталось уникальных цитат: {remaining}")
    
    conn.close()
    
except Exception as e:
    print(f"Ошибка: {e}")
