import sqlite3
import logging
import os
import psycopg2
from psycopg2.extras import DictCursor
from .biblia_config import DATABASE_PATH

logger = logging.getLogger(__name__)

class ChristianBotDB:
    def __init__(self):
        self.db_url = os.getenv('BIBLIA_DATABASE_URL')
        self.db_path = DATABASE_PATH
        self.is_postgres = self.db_url and self.db_url.startswith('postgres')
        self.init_database()
    
    def get_connection(self):
        if self.is_postgres:
            return psycopg2.connect(self.db_url)
        else:
            return sqlite3.connect(self.db_path)

    def init_database(self):
        """Инициализация базы данных"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Таблица для хранения чатов
                if self.is_postgres:
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS biblia_chats (
                            chat_id BIGINT PRIMARY KEY,
                            chat_title TEXT NOT NULL,
                            is_enabled BOOLEAN DEFAULT TRUE,
                            added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    ''')
                    cursor.execute('''
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
                else:
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS chats (
                            chat_id INTEGER PRIMARY KEY,
                            chat_title TEXT NOT NULL,
                            is_enabled BOOLEAN DEFAULT TRUE,
                            added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    ''')
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS quotes (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            text TEXT NOT NULL,
                            book TEXT NOT NULL,
                            chapter INTEGER,
                            verse TEXT,
                            used_count INTEGER DEFAULT 0,
                            added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    ''')
                
                conn.commit()
                logger.info("База данных Biblia инициализирована успешно")
                
        except Exception as e:
            logger.error(f"Ошибка при инициализации базы данных Biblia: {e}")
    
    def add_chat(self, chat_id: int, chat_title: str) -> bool:
        """Добавить чат в базу данных"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                table = "biblia_chats" if self.is_postgres else "chats"
                if self.is_postgres:
                    cursor.execute(
                        f"INSERT INTO {table} (chat_id, chat_title) VALUES (%s, %s) ON CONFLICT (chat_id) DO UPDATE SET chat_title = EXCLUDED.chat_title",
                        (chat_id, chat_title)
                    )
                else:
                    cursor.execute(
                        f"INSERT OR REPLACE INTO {table} (chat_id, chat_title) VALUES (?, ?)",
                        (chat_id, chat_title)
                    )
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Ошибка при добавлении чата Biblia: {e}")
            return False

    def remove_chat(self, chat_id: int) -> bool:
        """Удалить чат из базы данных"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                table = "biblia_chats" if self.is_postgres else "chats"
                placeholder = "%s" if self.is_postgres else "?"
                cursor.execute(f"DELETE FROM {table} WHERE chat_id = {placeholder}", (chat_id,))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Ошибка при удалении чата Biblia: {e}")
            return False

    def update_chat_settings(self, chat_id: int, is_enabled: bool) -> bool:
        """Обновить настройки чата"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                table = "biblia_chats" if self.is_postgres else "chats"
                placeholder = "%s" if self.is_postgres else "?"
                cursor.execute(
                    f"UPDATE {table} SET is_enabled = {placeholder} WHERE chat_id = {placeholder}",
                    (is_enabled, chat_id)
                )
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Ошибка при обновлении настроек чата Biblia: {e}")
            return False
    
    def get_random_quote(self):
        """Получить случайную цитату и обновить счетчик использований"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                table = "biblia_quotes" if self.is_postgres else "quotes"
                order_by = "RANDOM()"
                cursor.execute(f"SELECT id, text, book, chapter, verse FROM {table} ORDER BY {order_by} LIMIT 1")
                result = cursor.fetchone()
                if result:
                    quote_id = result[0]
                    # Обновляем счетчик использований
                    placeholder = "%s" if self.is_postgres else "?"
                    cursor.execute(f"UPDATE {table} SET used_count = used_count + 1 WHERE id = {placeholder}", (quote_id,))
                    conn.commit()
                    return {
                        'text': result[1],
                        'book': result[2],
                        'chapter': result[3],
                        'verse': result[4]
                    }
                return None
        except Exception as e:
            logger.error(f"Ошибка при получении случайной цитаты Biblia (is_postgres={self.is_postgres}): {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def add_quote(self, text: str, book: str, chapter: int, verse: str) -> bool:
        """Добавить цитату в базу данных"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                table = "biblia_quotes" if self.is_postgres else "quotes"
                placeholder = "%s" if self.is_postgres else "?"
                cursor.execute(
                    f"INSERT INTO {table} (text, book, chapter, verse) VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})",
                    (text, book, chapter, verse)
                )
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Ошибка при добавлении цитаты Biblia: {e}")
            return False
    
    def get_active_chats(self):
        """Получить все активные чаты (где включена рассылка)"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                table = "biblia_chats" if self.is_postgres else "chats"
                cursor.execute(f"SELECT chat_id FROM {table} WHERE is_enabled = TRUE")
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Ошибка при получении чатов Biblia: {e}")
            return []

    def get_all_quotes(self):
        """Получить все цитаты"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                table = "biblia_quotes" if self.is_postgres else "quotes"
                cursor.execute(f"SELECT id, text, book, chapter, verse, used_count, added_date FROM {table} ORDER BY id")
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Ошибка при получении всех цитат Biblia: {e}")
            return []

    def format_quote(self, quote_data):
        """Форматирование цитаты для отправки"""
        text = quote_data['text']
        book = quote_data['book']
        chapter = quote_data['chapter']
        verse = quote_data['verse']
        
        reference = f"{book}"
        if chapter:
            reference += f" {chapter}"
            if verse:
                reference += f":{verse}"
        
        return f"📖 *{reference}*\n\n{text}"