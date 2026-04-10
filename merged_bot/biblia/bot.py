import asyncio
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

from .biblia_db import ChristianBotDB
from .biblia_config import BOT_TOKEN, ADMIN_ID, DAILY_QUOTE_TIME, DAILY_QUOTE_TIMES

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class ChristianBot:
    def __init__(self):
        self.db = ChristianBotDB()
        self.application = Application.builder().token(BOT_TOKEN).build()
        self.setup_handlers()
        
    def setup_handlers(self):
        """Настройка обработчиков команд и сообщений"""
        
        # Основные команды
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("quote", self.send_quote_command))
        
        # Админские команды
        self.application.add_handler(CommandHandler("admin", self.admin_command))
        self.application.add_handler(CommandHandler("add_quote", self.add_quote_command))
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        self.application.add_handler(CommandHandler("broadcast", self.broadcast_command))
        
        # Команды управления чатом
        self.application.add_handler(CommandHandler("enable", self.enable_chat_command))
        self.application.add_handler(CommandHandler("disable", self.disable_chat_command))
        self.application.add_handler(CommandHandler("settings", self.settings_command))
        
        # Обработчики callback-ов от кнопок
        self.application.add_handler(CallbackQueryHandler(self.button_handler))
        
        # Обработчик добавления в группу
        self.application.add_handler(MessageHandler(
            filters.StatusUpdate.NEW_CHAT_MEMBERS, self.new_chat_member
        ))
        
        # Обработчик удаления из группы
        self.application.add_handler(MessageHandler(
            filters.StatusUpdate.LEFT_CHAT_MEMBER, self.left_chat_member
        ))
        
        # ЛОГИРОВАНИЕ ВСЕХ СООБЩЕНИЙ (для отладки)
        self.application.add_handler(MessageHandler(
            filters.TEXT & (~filters.COMMAND), self.log_all_messages
        ))
    
    async def log_all_messages(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Логирование любого текстового сообщения для проверки связи"""
        user = update.effective_user
        logger.info(f"✨ Библия_Бот: Получено сообщение от {user.id} ({user.first_name}): {update.message.text[:50]}")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        chat_id = update.effective_chat.id
        user = update.effective_user
        
        # Добавляем чат в базу данных
        chat_title = update.effective_chat.title or f"Чат с {user.first_name}"
        self.db.add_chat(chat_id, chat_title)
        
        welcome_text = f"""
📖 *Добро пожаловать в "Библия Ежедневно"!*

Здравствуйте, {user.first_name}! Этот бот присылает библейские цитаты каждый день в выбранное время.

💡 *Совет:* Добавьте меня в вашу группу или чат с друзьями! Я буду присылать Слово Божье всем участникам в удобное для вас время.

📖 *Что умеет бот:*
• Отправляет библейские цитаты в назначенное время
• Работает в личных чатах и группах
• Позволяет получить цитату по запросу
• Настраивается администраторами

🔧 *Основные команды:*
/quote - получить случайную библейскую цитату
/help - помощь по использованию
/settings - настройки чата (для админов)

Да благословит вас Господь! 🙏
        """
        
        keyboard = [
            [InlineKeyboardButton("📖 Получить цитату", callback_data="get_quote")],
            [InlineKeyboardButton("⚙️ Настройки", callback_data="settings")],
            [InlineKeyboardButton("ℹ️ Помощь", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_text, 
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        help_text = """
📚 *Помощь по использованию "Библия Ежедневно"*

🔹 *Основные команды:*
/start - начать работу с ботом
/quote - получить случайную библейскую цитату
/help - показать эту помощь

🔹 *Команды для администраторов чата:*
/enable - включить автоматическую отправку цитат
/disable - отключить автоматическую отправку
/settings - настройки времени отправки

🔹 *Команды для администратора бота:*
/admin - панель администратора
/add_quote - добавить новую цитату
/stats - статистика использования
/broadcast - рассылка сообщения всем чатам

📖 *Использование в группах:*
1. Добавьте бота в группу
2. Дайте ему права администратора (для отправки сообщений)
3. Используйте /enable для включения автоматических цитат
4. Настройте время отправки через /settings

🙏 *О боте:*
Этот бот создан для распространения Слова Божьего и духовного назидания верующих. Все цитаты взяты из Священного Писания.

Да благословит вас Господь!
        """
        
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
    
    async def send_quote_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /quote"""
        await self.send_random_quote(update.effective_chat.id, context)
    
    async def admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Панель администратора"""
        user_id = update.effective_user.id
        
        if user_id != ADMIN_ID:
            await update.message.reply_text("❌ У вас нет прав администратора.")
            return
        
        keyboard = [
            [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")],
            [InlineKeyboardButton("➕ Добавить цитату", callback_data="admin_add_quote")],
            [InlineKeyboardButton("📢 Рассылка", callback_data="admin_broadcast")],
            [InlineKeyboardButton("📋 Список чатов", callback_data="admin_chats")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🔧 *Панель администратора*\nВыберите действие:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def add_quote_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Добавление новой цитаты (только для админа)"""
        user_id = update.effective_user.id
        
        if user_id != ADMIN_ID:
            await update.message.reply_text("❌ У вас нет прав для добавления цитат.")
            return
        
        if not context.args or len(context.args) < 2:
            await update.message.reply_text(
                "📝 *Формат добавления цитаты:*\n"
                "`/add_quote \"Текст цитаты\" \"Книга\" глава стих`\n\n"
                "*Пример:*\n"
                "`/add_quote \"Бог есть любовь\" \"1-е Иоанна\" 4 8`",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        try:
            # Парсим аргументы
            full_text = " ".join(context.args)
            parts = full_text.split('"')
            
            if len(parts) < 4:
                raise ValueError("Неверный формат")
            
            quote_text = parts[1]
            book = parts[3]
            
            # Ищем главу и стих в оставшемся тексте
            remaining = parts[4].strip().split()
            chapter = int(remaining[0]) if remaining and remaining[0].isdigit() else None
            verse = remaining[1] if len(remaining) > 1 else None
            
            if self.db.add_quote(quote_text, book, chapter, verse):
                await update.message.reply_text(
                    f"✅ Цитата успешно добавлена!\n"
                    f"📖 {book} {chapter}:{verse if verse else ''}\n"
                    f"💬 {quote_text[:100]}..."
                )
            else:
                await update.message.reply_text("❌ Ошибка при добавлении цитаты.")
        
        except Exception as e:
            await update.message.reply_text(
                f"❌ Ошибка: {str(e)}\n"
                "Проверьте формат команды."
            )
    
    async def enable_chat_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Включить автоматическую отправку цитат в чате"""
        chat_id = update.effective_chat.id
        user = update.effective_user
        
        # Проверяем права администратора в группе
        if update.effective_chat.type in ['group', 'supergroup']:
            chat_member = await context.bot.get_chat_member(chat_id, user.id)
            if chat_member.status not in ['administrator', 'creator']:
                await update.message.reply_text(
                    "❌ Только администраторы чата могут управлять настройками бота."
                )
                return
        
        if self.db.update_chat_settings(chat_id, is_enabled=True):
            await update.message.reply_text(
                "✅ Автоматическая отправка библейских цитат включена!\n"
                f"⏰ Время отправки: {DAILY_QUOTE_TIME}\n"
                "Используйте /settings для изменения времени."
            )
        else:
            await update.message.reply_text("❌ Ошибка при обновлении настроек.")
    
    async def disable_chat_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Отключить автоматическую отправку цитат в чате"""
        chat_id = update.effective_chat.id
        user = update.effective_user
        
        # Проверяем права администратора в группе
        if update.effective_chat.type in ['group', 'supergroup']:
            chat_member = await context.bot.get_chat_member(chat_id, user.id)
            if chat_member.status not in ['administrator', 'creator']:
                await update.message.reply_text(
                    "❌ Только администраторы чата могут управлять настройками бота."
                )
                return
        
        if self.db.update_chat_settings(chat_id, is_enabled=False):
            await update.message.reply_text(
                "❌ Автоматическая отправка библейских цитат отключена.\n"
                "Используйте /enable для включения."
            )
        else:
            await update.message.reply_text("❌ Ошибка при обновлении настроек.")
    
    async def settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Настройки чата"""
        chat_id = update.effective_chat.id
        
        keyboard = [
            [InlineKeyboardButton("⏰ Изменить время", callback_data="set_time")],
            [InlineKeyboardButton("✅ Включить", callback_data="enable_chat")],
            [InlineKeyboardButton("❌ Отключить", callback_data="disable_chat")],
            [InlineKeyboardButton("📖 Получить цитату", callback_data="get_quote")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "⚙️ *Настройки чата*\n"
            f"Текущее время отправки: {DAILY_QUOTE_TIME}\n"
            "Выберите действие:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик нажатий на кнопки"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "get_quote":
            await self.send_random_quote(query.message.chat_id, context)
        
        elif query.data == "help":
            await self.help_command(update, context)
        
        elif query.data == "settings":
            await self.settings_command(update, context)
        
        elif query.data == "enable_chat":
            await self.enable_chat_command(update, context)
        
        elif query.data == "disable_chat":
            await self.disable_chat_command(update, context)
        
        elif query.data == "admin_stats":
            await self.show_admin_stats(query, context)
    
    async def send_random_quote(self, chat_id: int, context=None):
        """Отправить случайную цитату в чат"""
        try:
            # Получаем объект бота из контекста или напрямую
            bot = context.bot if hasattr(context, 'bot') else context
            if bot is None:
                bot = self.application.bot

            quote_data = self.db.get_random_quote()
            
            if quote_data:
                formatted_quote = self.db.format_quote(quote_data)
                try:
                    # Пытаемся отправить с Markdown
                    await bot.send_message(
                        chat_id=chat_id,
                        text=formatted_quote,
                        parse_mode=ParseMode.MARKDOWN
                    )
                except Exception as e:
                    logger.warning(f"Ошибка Markdown, отправляем обычным текстом: {e}")
                    # Если Markdown не прошел, отправляем обычным текстом
                    await bot.send_message(
                        chat_id=chat_id,
                        text=formatted_quote.replace("*", "").replace("_", "")
                    )
            else:
                await bot.send_message(
                    chat_id=chat_id,
                    text="😔 Извините, не удалось получить цитату из базы данных."
                )
        except Exception as e:
            logger.error(f"Критическая ошибка в send_random_quote: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    async def show_admin_stats(self, query, context: ContextTypes.DEFAULT_TYPE):
        """Показать статистику администратору"""
        quotes = self.db.get_all_quotes()
        active_chats = self.db.get_active_chats()
        
        stats_text = f"""
📊 *Статистика бота*

📖 Всего цитат в базе: {len(quotes)}
👥 Активных чатов: {len(active_chats)}
📅 Время работы: {datetime.now().strftime('%d.%m.%Y %H:%M')}

📈 *Топ-5 популярных цитат:*
        """
        
        # Сортируем цитаты по количеству использований
        sorted_quotes = sorted(quotes, key=lambda x: x[5], reverse=True)[:5]
        
        for i, quote in enumerate(sorted_quotes, 1):
            book = quote[2]
            chapter = quote[3]
            verse = quote[4]
            used_count = quote[5]
            stats_text += f"{i}. {book} {chapter}:{verse} ({used_count} раз)\n"
        
        await query.edit_message_text(
            stats_text,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def new_chat_member(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик добавления бота в чат"""
        new_members = update.message.new_chat_members
        bot_added = any(member.id == context.bot.id for member in new_members)
        
        if bot_added:
            chat_id = update.effective_chat.id
            chat_title = update.effective_chat.title
            
            self.db.add_chat(chat_id, chat_title)
            
            welcome_message = """
📖 *Благодарю за добавление в чат!*

Я - "Библия Ежедневно", присылаю библейские цитаты каждый день в выбранное время.

📖 *Чтобы начать получать цитаты:*
1. Дайте мне права администратора (для отправки сообщений)
2. Используйте команду /enable
3. Настройте время отправки через /settings

🔧 *Полезные команды:*
/quote - получить цитату сейчас
/help - помощь по использованию
/settings - настройки чата

Да благословит Господь этот чат! 🙏
            """
            
            await update.message.reply_text(
                welcome_message,
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def left_chat_member(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик удаления бота из чата"""
        left_member = update.message.left_chat_member
        
        if left_member and left_member.id == context.bot.id:
            chat_id = update.effective_chat.id
            self.db.remove_chat(chat_id)
            logger.info(f"Бот удален из чата {chat_id}")
    
    def setup_jobs(self):
        """Настройка ежедневной отправки цитат"""
        import datetime
        from zoneinfo import ZoneInfo
        
        job_queue = self.application.job_queue
        if not job_queue:
            logger.error("❌ JobQueue не инициализирован. Планировщик не будет работать!")
            return
            
        try:
            try:
                time_parts_list = [t.strip() for t in DAILY_QUOTE_TIMES]
            except NameError:
                time_parts_list = [DAILY_QUOTE_TIME]
            tz = ZoneInfo('Europe/Moscow')
            
            for time_str in time_parts_list:
                try:
                    parts = time_str.split(':')
                    t = datetime.time(hour=int(parts[0]), minute=int(parts[1]), tzinfo=tz)
                    job_queue.run_daily(self._send_daily_quotes_job, time=t)
                    logger.info(f"⌚️ Планировщик цитат ptb запущен на {time_str} (МСК)")
                except Exception as ex:
                    logger.error(f"Не удалось распарсить время {time_str}: {ex}")
                    
            logger.info("✅ Планировщик полностью настроен.")
        except Exception as e:
            logger.error(f"❌ Ошибка при настройке планировщика: {e}")
            
    async def _send_daily_quotes_job(self, context: ContextTypes.DEFAULT_TYPE):
        """Рассылка цитат по расписанию через JobQueue"""
        active_chats = self.db.get_active_chats()
        
        if not active_chats:
            logger.info("Нет активных чатов для отправки цитат")
            return
            
        logger.info(f"Отправка ежедневных цитат в {len(active_chats)} чатов по расписанию")
        
        for chat_id in active_chats:
            try:
                await self.send_random_quote(chat_id, context.bot)
                await asyncio.sleep(1)  # Небольшая задержка "анти-спам"
            except Exception as e:
                logger.error(f"Ошибка при отправке расписания в {chat_id}: {e}")
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда для просмотра статистики (только для админа)"""
        user_id = update.effective_user.id
        
        if user_id != ADMIN_ID:
            await update.message.reply_text("❌ У вас нет прав для просмотра статистики.")
            return
        
        quotes = self.db.get_all_quotes()
        active_chats = self.db.get_active_chats()
        
        stats_text = f"""
📊 *Статистика бота*

📖 Всего цитат в базе: {len(quotes)}
👥 Активных чатов: {len(active_chats)}
📅 Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}

🔥 *Самые популярные цитаты:*
        """
        
        # Показываем топ-3 популярных цитат
        sorted_quotes = sorted(quotes, key=lambda x: x[5], reverse=True)[:3]
        
        for i, quote in enumerate(sorted_quotes, 1):
            book = quote[2]
            chapter = quote[3] or ""
            verse = quote[4] or ""
            used_count = quote[5]
            reference = f"{book} {chapter}:{verse}".strip()
            stats_text += f"{i}. {reference} - использована {used_count} раз\n"
        
        await update.message.reply_text(stats_text, parse_mode=ParseMode.MARKDOWN)
    
    async def broadcast_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Рассылка сообщения всем чатам (только для админа)"""
        user_id = update.effective_user.id
        
        if user_id != ADMIN_ID:
            await update.message.reply_text("❌ У вас нет прав для рассылки.")
            return
        
        if not context.args:
            await update.message.reply_text(
                "📢 *Формат рассылки:*\n"
                "`/broadcast Ваше сообщение`\n\n"
                "*Пример:*\n"
                "`/broadcast Дорогие братья и сестры! Поздравляем с праздником!`",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        message_text = " ".join(context.args)
        active_chats = self.db.get_active_chats()
        
        if not active_chats:
            await update.message.reply_text("❌ Нет активных чатов для рассылки.")
            return
        
        success_count = 0
        
        for chat_id in active_chats:
            try:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"📢 *Сообщение от администратора:*\n\n{message_text}",
                    parse_mode=ParseMode.MARKDOWN
                )
                success_count += 1
                await asyncio.sleep(1)  # Задержка между отправками
            except Exception as e:
                logger.error(f"Ошибка при отправке в чат {chat_id}: {e}")
        
        await update.message.reply_text(
            f"✅ Рассылка завершена!\n"
            f"📤 Отправлено в {success_count} из {len(active_chats)} чатов."
        )
    
    def run(self):
        """Запуск бота"""
        logger.info("Запуск Христианского бота...")
        
        # Запускаем планировщик
        self.setup_jobs()
        
        # Запускаем бота
        logger.info("Бот готов к работе!")
        self.application.run_polling(drop_pending_updates=True)

def main():
    """Главная функция"""
    if BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
        print("❌ Ошибка: Необходимо установить BOT_TOKEN в файле .env")
        return
    
    bot = ChristianBot()
    bot.run()

if __name__ == "__main__":
    main()
