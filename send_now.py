import asyncio
import os
import sys
from dotenv import load_dotenv
from telegram import Bot

# Добавляем путь для импорта biblia_db
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from merged_bot.biblia.biblia_db import ChristianBotDB

async def send_manual_quote():
    load_dotenv()
    token = os.getenv("BIBLIA_BOT_TOKEN")
    if not token:
        print("Token not found")
        return
        
    chat_id = -1003664481014 # ID из логов
    
    db = ChristianBotDB()
    quote_data = db.get_random_quote()
    
    if quote_data:
        text = db.format_quote(quote_data)
        text += "\n\n*(Отправлено вручную по запросу создателя ✨)*"
        bot = Bot(token=token)
        await bot.send_message(chat_id=chat_id, text=text, parse_mode='Markdown')
        print("Цитата успешно отправлена!")
    else:
        print("Цитата не найдена в БД.")

if __name__ == "__main__":
    asyncio.run(send_manual_quote())
