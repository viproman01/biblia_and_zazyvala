import asyncio
import os
import sys
from dotenv import load_dotenv
from telegram import Bot

# Добавляем путь для импорта biblia_db
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from merged_bot.biblia.biblia_db import ChristianBotDB

async def broadcast_quote():
    load_dotenv()
    token = os.getenv("BIBLIA_BOT_TOKEN")
    if not token:
        print("Token not found")
        return
        
    db = ChristianBotDB()
    bot = Bot(token=token)
    
    active_chats = db.get_active_chats()
    print(f"Найдено {len(active_chats)} активных чатов.")
    
    quote_data = db.get_random_quote()
    if not quote_data:
        print("Цитата не найдена в БД.")
        return
        
    # Формируем только чистый текст цитаты (без лишних надписей)
    text = db.format_quote(quote_data)
    
    success = 0
    for chat_id in active_chats:
        try:
            await bot.send_message(chat_id=chat_id, text=text, parse_mode='Markdown')
            success += 1
        except Exception as e:
            print(f"Ошибка отправки в {chat_id}: {e}")
            
    print(f"Цитата успешно отправлена в {success} чатов из {len(active_chats)}!")

if __name__ == "__main__":
    asyncio.run(broadcast_quote())
