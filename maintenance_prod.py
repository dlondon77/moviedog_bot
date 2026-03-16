import logging
import os
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters
)

# Токен берется из переменных окружения (настройте в панели Bothost)
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
# URL картинки для режима обслуживания (можно тоже через переменные окружения)
MAINTENANCE_IMAGE_URL = os.environ.get('MAINTENANCE_IMAGE_URL', 'https://example.com/maintenance.jpg')

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

async def maintenance_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Единый обработчик для всех команд в режиме обслуживания"""
    message = (
        "🐾 <b>Гав-гав! КиноИщейка на плановом техобслуживании!</b>\n\n"
        "Прямо сейчас я:\n"
        "• Чищу зубы от попкорна 🦷🍿\n"
        "• Расчесываю шерсть после марафона ужастиков 👻\n"
        "• Перезагружаю свой собачий процессор 🐕💻\n\n"
        "Но скоро я вернусь с обновленным нюхом на кино!\n"
        "Попробуй зайти чуть позже, я уже почти закончила!"
    )
    
    try:
        await update.message.reply_photo(
            photo=MAINTENANCE_IMAGE_URL,
            caption=message,
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Ошибка при отправке картинки: {e}")
        await update.message.reply_text(message, parse_mode='HTML')

def main():
    if not TELEGRAM_TOKEN:
        logger.error("Токен не найден! Добавьте TELEGRAM_TOKEN в переменные окружения")
        return
    
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    commands = ["start", "about", "random", "search", "premiers", "person", "feedback", "faq"]
    for cmd in commands:
        application.add_handler(CommandHandler(cmd, maintenance_mode))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, maintenance_mode))

    logger.info("🚀 Бот в режиме обслуживания запущен на Bothost")
    application.run_polling()

if __name__ == '__main__':
    main()
