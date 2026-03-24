from dotenv import load_dotenv

# Загружаем переменные окружения ПЕРВЫМ делом
load_dotenv()

import asyncio
import logging
import os
import sys
from aiohttp import web

# Добавляем пути к ботам
sys.path.append(os.path.dirname(__file__))

# Импортируем ботов
try:
    from zazyvala.bot import main as start_zazyvala
    from biblia.bot import ChristianBot
except ImportError as e:
    print(f"Ошибка импорта: {e}")
    sys.exit(1)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("UnifiedRunner")

async def start_health_server():
    """Сервер проверки здоровья для Render/HF"""
    async def handle_health(request):
        return web.Response(text="OK", status=200)

    app = web.Application()
    app.router.add_get("/", handle_health)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    try:
        site = web.TCPSite(runner, "0.0.0.0", port)
        await site.start()
        logger.info(f"✅ Health server started on PORT: {port}")
    except Exception as e:
        logger.error(f"❌ Failed to start health server on port {port}: {e}")

async def run_biblia():
    """Запуск Христианского бота"""
    try:
        token = os.getenv("BIBLIA_BOT_TOKEN")
        if not token:
            logger.error("❌ BIBLIA_BOT_TOKEN не найден!")
            return

        logger.info("🔧 Инициализация ChristianBot...")
        bot = ChristianBot()
        
        # Переопределяем токен
        bot.application = bot.application.builder().token(token).build()
        bot.setup_handlers()
        
        logger.info("🚀 Запуск Biblia_Bot.start()...")
        await bot.application.initialize()
        await bot.application.start()
        
        logger.info("📡 Biblia_Bot: запускаем polling...")
        await bot.application.updater.start_polling(drop_pending_updates=True)
        logger.info("✅ Biblia_Bot: ПОЛЛИНГ ЗАПУЩЕН!")
        # Держим задачу запущенной и пишем пульс
        while True:
            await asyncio.sleep(600)  # Раз в 10 минут
            logger.info("💓 Библия_Бот: Поллинг активен...")
    except Exception as e:
        logger.error(f"❌ Ошибка в Библия_Бот: {e}")
        import traceback
        logger.error(traceback.format_exc())

async def main():
    """Главная функция запуска обоих ботов"""
    logger.info("🤖 Запуск объединенного сервера ботов...")
    
    # Диагностика переменных (безопасно)
    logger.info(f"📝 Проверка конфигурации:")
    logger.info(f"   - BOT_TOKEN: {'✅ задан' if os.getenv('BOT_TOKEN') else '❌ ОТСУТСТВУЕТ'}")
    logger.info(f"   - BIBLIA_BOT_TOKEN: {'✅ задан' if os.getenv('BIBLIA_BOT_TOKEN') else '❌ ОТСУТСТВУЕТ'}")
    logger.info(f"   - DATABASE_URL: {'✅ задана' if os.getenv('DATABASE_URL') else '❌ ОТСУТСТВУЕТ'}")
    logger.info(f"   - PORT: {os.getenv('PORT')}")
    
    # Запускаем сервер здоровья
    await start_health_server()
    
    # Запускаем задачи для обоих ботов
    # Для Zazyvala используем его функцию main, но без его собственного health_server
    # (поэтому в его коде стоит проверка if os.getenv("RENDER"))
    
    tasks = [
        asyncio.create_task(start_zazyvala(run_health=False)), # Бот Зазывала
        asyncio.create_task(run_biblia())                      # Бот Библия
    ]
    
    logger.info("📡 Поллинг запущен для обоих ботов. Ожидаем сообщения...")
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Остановка сервера...")
