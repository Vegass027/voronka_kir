import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from src.config import BOT_TOKEN
from src.db.engine import async_session_factory
from src.middlewares.db import DbSessionMiddleware
from src.handlers import user_handlers, admin_handlers

# Настройка логирования для вывода информационных сообщений
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    """Основная функция для запуска бота."""
    # Инициализация бота с токеном и новыми свойствами по умолчанию
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    
    # Использование MemoryStorage для хранения состояний FSM в памяти
    storage = MemoryStorage()
    
    # Инициализация диспетчера
    dp = Dispatcher(storage=storage)

    # Регистрация middleware для сессий базы данных.
    # Он будет применяться ко всем `update` (сообщениям, колбэкам и т.д.)
    dp.update.middleware(DbSessionMiddleware(session_pool=async_session_factory))

    # Регистрируем роутеры
    dp.include_router(admin_handlers.router) # Админский роутер должен идти первым
    dp.include_router(user_handlers.router)

    logger.info("Запуск бота...")

    # Принудительно сбрасываем любую другую активную сессию
    await bot.set_webhook(url="")
    await bot.delete_webhook(drop_pending_updates=True)
    
    # Запускаем long polling
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        # Запускаем асинхронную функцию main
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        # Обработка чистого выхода при нажатии Ctrl+C
        logger.info("Бот остановлен.")
