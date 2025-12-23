import asyncio
import logging
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from src.db.engine import engine, DB_URL

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    """
    Основная функция для проверки соединения с БД.
    """
    if not DB_URL:
        logger.error("Переменная окружения DATABASE_URL не найдена. Проверьте .env файл.")
        return

    logger.info("Запуск проверки соединения с базой данных...")
    logger.info(f"Используется URL: ...{DB_URL[-50:]}")
    
    try:
        async with engine.connect() as connection:
            logger.info("✅ Соединение с базой данных успешно установлено.")
            
            result = await connection.execute(text("SELECT 1"))
            if result.scalar_one() == 1:
                logger.info("✅ Тестовый запрос 'SELECT 1' успешно выполнен.")
            else:
                logger.warning("⚠️ Тестовый запрос 'SELECT 1' вернул неожиданный результат.")

    except Exception as e:
        logger.error(f"❌ Произошла ошибка: {e}", exc_info=True)
    finally:
        await engine.dispose()
        logger.info("Ресурсы движка освобождены. Проверка завершена.")


if __name__ == "__main__":
    asyncio.run(main())