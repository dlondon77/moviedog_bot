# moviedog_bot_vk_dev.py
import os
import configparser
import logging
from core.vk_adapter import VKAdapter

# Определяем базовую директорию (корень проекта)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, 'config', 'config.ini')

# Загружаем конфиг
config = configparser.ConfigParser()
config.read(CONFIG_PATH)

# Путь для логов
LOG_PATH = os.path.join(BASE_DIR, 'logs', 'bot_vk.log')

# Создаем папку для логов, если её нет
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('vk_bot')

def main():
    # Получаем настройки VK (сначала из переменных окружения, потом из конфига)
    VK_TOKEN = os.environ.get('VK_ACCESS_TOKEN') or config['VK']['access_token']
    GROUP_ID = int(os.environ.get('VK_GROUP_ID') or config['VK']['group_id'])
    
    # Проверяем, что токен загружен
    if not VK_TOKEN:
        logger.error("VK_TOKEN не найден! Добавьте VK_ACCESS_TOKEN в переменные окружения или config.ini")
        return
    
    logger.info(f"🚀 Запуск VK-бота для группы {GROUP_ID}")
    
    try:
        adapter = VKAdapter(VK_TOKEN, GROUP_ID)
        adapter.run()
    except Exception as e:
        logger.error(f"Ошибка запуска VK-бота: {e}", exc_info=True)

if __name__ == '__main__':
    main()
