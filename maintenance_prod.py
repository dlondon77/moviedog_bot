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

# URL картинки (прямо в коде, без конфига)
# Здесь нужно будет заменить на новую картинку с переездом
MAINTENANCE_IMAGE_URL = "https://i.postimg.cc/9Q9q1dYW/image.jpg"

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

async def maintenance_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Единый обработчик для всех команд в режиме обслуживания"""
    message = (
        "🐾 <b>Гав-гав! КиноИщейка переезжает!</b>\n\n"
        "Прямо сейчас я:\n"
        "• Упаковываю кинопленку в коробки 📦\n"
        "• Собираю чемодан с попкорном 🍿\n"
        "• Ищу новый уютный домик для своих обзоров 🏠\n\n"
        "<b>Пока я пакую вещи, вы можете найти меня здесь:</b>\n\n"
        "📱 <b>Другие площадки:</b>\n"
        "• <a href='https://max.ru/join/6Gr8OAJgFYvmtDwSQE7xZKtZBYRyKYbUnGEk6RIklJY'>Канал в Max</a> – первые обзоры уже там!\n"
        "• <a href='https://vk.com/club235550414'>Сообщество ВКонтакте</a> – общаемся, спорим, обсуждаем\n"
        "• <a href='https://vk.com/im/channels/-235633316'>Канал в VK</a> – новости и анонсы\n"
        "• <a href='https://vk.me/movie_dog?ref=start'>Бот в VK</a> – работает без перебоев!\n\n"
        "🐕 <b>Telegram-канал:</b>\n"
        "• <a href='https://t.me/Movie_dog_channel'>КиноИщейка в Telegram</a> – скоро вернусь!\n\n"
        "<b>Заглядывайте в гости на других площадках, а здесь я откроюсь с обновленным интерьером!</b> 🌟"
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
