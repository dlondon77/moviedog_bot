# moviedog_bot_vk.py
import configparser
import logging
from core.vk_adapter import VKAdapter

# Загружаем конфиг
config = configparser.ConfigParser()
config.read('/volume1/homes/Dima/tgbots/moviedog/dev/config/config.ini')

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler('/volume1/homes/Dima/tgbots/moviedog/dev/logs/bot_vk.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('vk_bot')

def main():
    # Получаем настройки VK из конфига
    VK_TOKEN = config['VK']['access_token']
    GROUP_ID = int(config['VK']['group_id'])
    
    logger.info("🚀 Запуск VK-бота")
    adapter = VKAdapter(VK_TOKEN, GROUP_ID)
    adapter.run()

if __name__ == '__main__':
    main()
