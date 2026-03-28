import os
import traceback
import psycopg2
from dotenv import load_dotenv

load_dotenv()
url = os.getenv('BIBLIA_DATABASE_URL') or os.getenv('DATABASE_URL')

try:
    conn = psycopg2.connect(url)
    cursor = conn.cursor()
    cursor.execute("SELECT id, text, book, chapter, verse FROM biblia_quotes ORDER BY RANDOM() LIMIT 1")
    result = cursor.fetchone()
    print("Результат запроса RANDOM():", result)
    
    if result:
        quote_id = result[0]
        cursor.execute("UPDATE biblia_quotes SET used_count = used_count + 1 WHERE id = %s", (quote_id,))
        conn.commit()
        print("UPDATE успешен!")
        
    conn.close()
except Exception as e:
    print(f"Ошибка: {e}")
    traceback.print_exc()
