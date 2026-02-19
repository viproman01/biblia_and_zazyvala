import asyncio
import random
import logging
import os
from datetime import datetime

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, ChatMemberUpdatedFilter, IS_MEMBER, IS_NOT_MEMBER
from aiogram.types import ChatMemberUpdated
from aiogram.enums import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from aiohttp import web

import config
import database as db

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler()


def get_user_name(user: types.User) -> str:
    """Получить имя пользователя для приветствия"""
    if user.first_name:
        name = user.first_name
        if user.last_name:
            name += f" {user.last_name}"
    elif user.username:
        name = f"@{user.username}"
    else:
        name = "Новый участник"
    return name


def create_mention(user_id: int, first_name: str, username: str = None) -> str:
    """Создать упоминание пользователя через случайный эмодзи"""
    emoji = random.choice(config.MENTION_EMOJIS)
    # Используем HTML-формат для скрытого упоминания в эмодзи
    return f'<a href="tg://user?id={user_id}">{emoji}</a>'


# Обработчики команд будут ниже...


@dp.chat_member(ChatMemberUpdatedFilter(IS_NOT_MEMBER >> IS_MEMBER))
async def on_user_join(event: ChatMemberUpdated):
    """Обработка входа нового участника"""
    user = event.new_chat_member.user
    
    if user.is_bot:
        return
    
    # Сохраняем в базу (гарантированный захват при входе)
    await db.add_member(
        user_id=user.id,
        username=user.username or "",
        first_name=user.first_name or "",
        last_name=user.last_name or "",
        chat_id=event.chat.id
    )
    
    logger.info(f"Захвачен новый участник при входе: {get_user_name(user)} (ID: {user.id})")


@dp.chat_member(ChatMemberUpdatedFilter(IS_MEMBER >> IS_NOT_MEMBER))
async def on_user_leave(event: ChatMemberUpdated):
    """Обработка выхода участника"""
    user = event.old_chat_member.user
    
    if user.is_bot:
        return
    
    await db.remove_member(user.id, event.chat.id)
    logger.info(f"Участник ушёл: {get_user_name(user)} (ID: {user.id})")


# ==================== ГЛАВНАЯ КОМАНДА - ЗАЗВАТЬ ВСЕХ ====================

@dp.message(Command("call", "зазвать", "all", "everyone"))
async def cmd_call_everyone(message: types.Message):
    """🔔 ЗАЗВАТЬ ВСЕХ УЧАСТНИКОВ ЧАТА ЧЕРЕЗ ЭМОДЗИ"""
    
    if message.chat.type == "private":
        await message.answer("⚠️ Эта команда работает только в групповых чатах!")
        return
    
    member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    is_admin = member.status in ["creator", "administrator"]
    is_global_admin = message.from_user.id == config.ADMIN_ID
    
    if not is_admin and not is_global_admin:
        await message.answer("⛔ Только администраторы могут зазывать всех!")
        return
    
    members = await db.get_chat_members(message.chat.id)
    
    if not members:
        await message.answer(
            "👥 Список участников пуст!\n\n"
            "Бот собирает участников из сообщений или при их входе в чат. "
            "Также можно использовать /register."
        )
        return
    
    command_text = message.text.split(maxsplit=1)
    custom_message = command_text[1] if len(command_text) > 1 else None
    
    # Формируем список упоминаний-эмодзи
    mentions = []
    for user_id, username, first_name, last_name in members:
        if user_id == message.from_user.id:
            continue
        mentions.append(create_mention(user_id, first_name, username))
    
    if not mentions:
        await message.answer("👥 Некого зазывать — в базе только вы!")
        return
    
    call_message = custom_message or random.choice(config.CALL_MESSAGES)
    
    # Группируем по 50 эмодзи в сообщении
    chunk_size = 50
    mention_chunks = [mentions[i:i + chunk_size] for i in range(0, len(mentions), chunk_size)]
    
    try:
        # Отправляем основной текст и первое облако эмодзи
        await message.answer(
            f"📢 <b>{call_message}</b>\n\n{' '.join(mention_chunks[0])}", 
            parse_mode=ParseMode.HTML
        )
        
        # Отправляем остальные облака, если участников много
        for chunk in mention_chunks[1:]:
            await asyncio.sleep(0.5)
            await message.answer(' '.join(chunk), parse_mode=ParseMode.HTML)
        
        await db.log_message("call", message.chat.id)
        
    except Exception as e:
        logger.error(f"Ошибка при зазывании: {e}")


# ==================== ДОПОЛНИТЕЛЬНЫЕ КОМАНДЫ ====================

@dp.message(Command("register", "записаться"))
async def cmd_register(message: types.Message):
    """Добровольная регистрация в базу зазывалы"""
    await db.add_member(
        user_id=message.from_user.id,
        username=message.from_user.username or "",
        first_name=message.from_user.first_name or "",
        last_name=message.from_user.last_name or "",
        chat_id=message.chat.id
    )
    await message.answer("✅ Вы успешно записаны в базу 'Зазывалы'!")


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Команда /start"""
    global config
    
    if config.ADMIN_ID == 0:
        config.ADMIN_ID = message.from_user.id
        env_content = f"BOT_TOKEN={config.BOT_TOKEN}\nADMIN_ID={message.from_user.id}\n"
        with open(".env", "w") as f:
            f.write(env_content)
        
        await message.answer(
            f"🎯 <b>Администратор назначен!</b>\n\n"
            f"Ваш ID ({message.from_user.id}) сохранен как основной ID администратора.",
            parse_mode=ParseMode.HTML
        )
    
    await message.answer(
        "👋 Привет! Я бот-зазывала!\n\n"
        "🎯 Моя главная функция:\n"
        "📢 <b>/call</b> — зазвать ВСЕХ участников через облако эмодзи!\n\n"
        "📋 Команды:\n"
        "/register — записаться в базу (если вы 'молчун')\n"
        "/stats — статистика\n"
        "/members — список участников\n"
        "/help — справка",
        parse_mode=ParseMode.HTML
    )


@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    """Команда /help"""
    await message.answer(
        "📖 <b>Справка по боту-зазывале</b>\n\n"
        "<b>🔔 Главная команда:</b>\n"
        "<code>/call [текст]</code> — упомянуть всех через эмодзи\n\n"
        "<b>⚙️ Команды:</b>\n"
        "<code>/register</code> — записаться в базу вручную\n"
        "<code>/stats</code> — статистика чата\n"
        "<code>/members</code> — кто есть в базе\n\n"
        "<b>❓ Как это работает:</b>\n"
        "Бот запоминает всех, кто пишет, заходит в чат или нажимает /register. "
        "По команде /call он отправляет сообщение с эмодзи, где в каждый смайлик спрятано упоминание участника. "
        "Так чат не забивается именами, а уведомление получают все!",
        parse_mode=ParseMode.HTML
    )


@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    """Показать статистику"""
    stats = await db.get_stats(message.chat.id)
    await message.answer(
        f"📊 <b>Статистика чата</b>\n\n"
        f"👥 Участников в базе: {stats['member_count']}\n"
        f"📢 Зазываний: {stats['call_count']}\n"
        f"📨 Всего сообщений: {stats['total_messages']}",
        parse_mode=ParseMode.HTML
    )


@dp.message(Command("members"))
async def cmd_members(message: types.Message):
    """Показать список участников"""
    members = await db.get_chat_members(message.chat.id)
    
    if not members:
        await message.answer("👥 Список участников пуст.")
        return
    
    text = "👥 <b>Участники в базе:</b>\n\n"
    for i, (user_id, username, first_name, last_name) in enumerate(members[:30], 1):
        name = first_name or "Без имени"
        text += f"{i}. {name}" + (f" (@{username})\n" if username else "\n")
    
    if len(members) > 30:
        text += f"\n... и ещё {len(members) - 30}"
    
    text += f"\n\n<b>Всего:</b> {len(members)} чел."
    await message.answer(text, parse_mode=ParseMode.HTML)


# ==================== СБОР УЧАСТНИКОВ ====================

@dp.message(F.text)
async def collect_members(message: types.Message):
    """Собираем участников из всех сообщений в чате (если это не команда)"""
    logger.info(f"📩 Получено сообщение от {message.from_user.id} ({message.from_user.full_name}) в чате {message.chat.id}: {message.text[:50]}")
    
    if message.from_user.is_bot:
        return
    
    await db.add_member(
        user_id=message.from_user.id,
        username=message.from_user.username or "",
        first_name=message.from_user.first_name or "",
        last_name=message.from_user.last_name or "",
        chat_id=message.chat.id
    )


# ==================== ЗАПУСК БОТА ====================

from aiohttp import web

# ... (предыдущий код)

async def handle_health(request):
    return web.Response(text="OK")

async def start_health_server():
    app = web.Application()
    app.router.add_get("/", handle_health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.getenv("PORT", 8080)))
    await site.start()
    logger.info(f"Health server started on port {os.getenv('PORT', 8080)}")

async def main():
    """Главная функция запуска"""
    try:
        await db.init_db()
        logger.info("🚀 Бот-зазывала (Эмодзи-версия) запущен!")
        
        # Запускаем сервер для проверки здоровья (нужно для Render/HF)
        if os.getenv("RENDER"):
            await start_health_server()
            
        retry_count = 0
        max_retries = 10
        
        while retry_count < max_retries:
            try:
                logger.info(f"Начинаем polling... (Попытка {retry_count + 1}/{max_retries})")
                await dp.start_polling(bot, skip_updates=True)
                break
            except Exception as e:
                retry_count += 1
                logger.error(f" Ошибка подключения: {e}")
                if retry_count < max_retries:
                    wait_time = min(retry_count * 5, 60)
                    logger.info(f"Повтор через {wait_time} сек...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.critical("❌ Не удалось подключиться к Telegram после 10 попыток.")
    finally:
        await bot.session.close()
        logger.info("Бот остановлен")


if __name__ == "__main__":
    asyncio.run(main())

