import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Telegram Bot Configuration
# Используем специально выделенный токен для второго бота
BOT_TOKEN = os.getenv('BIBLIA_BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
ADMIN_ID = int(os.getenv('ADMIN_ID', '0'))

# Database Configuration
DATABASE_PATH = os.getenv('DATABASE_PATH', 'simple_bible_bot.db')

# Scheduler Configuration
DAILY_QUOTE_TIMES = os.getenv('BIBLIA_DAILY_QUOTE_TIMES', '09:00,21:00').split(',')
DAILY_QUOTE_TIME = os.getenv('BIBLIA_DAILY_QUOTE_TIME', DAILY_QUOTE_TIMES[0] if DAILY_QUOTE_TIMES else '08:00')
TIMEZONE = os.getenv('BIBLIA_TIMEZONE', 'Europe/Moscow')

# Список чатов, которые бот должен помнить всегда (даже после перезагрузки Render)
# Сюда нужно добавить ваш ID (число), например: PERSISTENT_CHATS = [-100123456789, 12345678]
PERSISTENT_CHATS = [
    -1003419922107, -1003048330602, -1002940234421, -1002780065173,
    -1002713111864, -1002692514973, -1002666591304, -1002657643762,
    -1002556520598, -1002547247073, -1002473497813, -1002471618888,
    -1002381651427, -1002354834213, -1002247297743, -1002102314164,
    -1002088397579, 1488335870, 5651796633
]

# Проверка обязательных переменных
if BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
    print("⚠️  ВНИМАНИЕ: Необходимо установить BOT_TOKEN в файле .env")
