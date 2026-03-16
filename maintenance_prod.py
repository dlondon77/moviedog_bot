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

# Токен из переменных окружения Bothost
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')

# Новая картинка с переездом
MAINTENANCE_IMAGE_URL = "https://i.postimg.cc/SxzFCnLH/Maintenance_02.jpg"

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

async def maintenance_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Единый обработчик для всех команд в режиме переезда"""
    message = (
        "🐾 <b>Гав! КиноИщейка собирает чемоданы!</b>\n\n"
        "Друзья, я временно переезжаю в новое собачье пространство (читай: на новый сервер). Прямо сейчас я:\n"
        "• Упаковываю кинопленки в коробки 📦\n"
        "• Собираю чемодан с попкорном 🍿\n"
        "• Перенастраиваю киноискательные бизнес-процессы\n\n"
        "Но главная новость: я уже открыла новую кинолабораторию в VK\n\n"
        "🤖 <b>КиноИщейка в VK</b> – <a href='https://vk.me/movie_dog?ref=start'>@movie_dog</a>\n"
        "Работает в бета-версии, но уже умеет искать фильмы и давать свои хвостатые мнения. Функций пока чуть меньше, чем в Telegram, но я активно учусь новым командам!\n\n"
        "📱 <b>Не забывайте о том, что меня ещё можно читать:</b>\n"
        "• <a href='https://max.ru/join/6Gr8OAJgFYvmtDwSQE7xZKtZBYRyKYbUnGEk6RIklJY'>Канал в Max</a>\n"
        "• <a href='https://vk.com/club235550414'>Сообщество ВКонтакте</a>\n"
        "• <a href='https://vk.com/im/channels/-235633316'>Канал в VK</a>\n"
        "• и пока <a href='https://t.me/Movie_dog_channel'>Telegram-канал</a>\n\n"
        "Сюда я скоро вернусь с новыми силами и обновлённым нюхом!\n"
        "А пока бегите знакомиться с VK-КиноИщейкой – я уже заждалась! 🐕💨"
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
        logger.error("Токен не найден! Добавьте TELEGRAM_TOKEN в переменные окружения Bothost")
        return
    
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Все команды
    commands = ["start", "about", "random", "search", "premiers", "person", "feedback", "faq"]
    for cmd in commands:
        application.add_handler(CommandHandler(cmd, maintenance_mode))

    # Все текстовые сообщения
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, maintenance_mode))

    logger.info("🚀 Бот в режиме переезда запущен на Bothost")
    application.run_polling()

if __name__ == '__main__':
    main()
