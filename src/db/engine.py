import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from src.config import DB_URL
from src.db.base import Base
# Импортируем модели, чтобы они были зарегистрированы в Base.metadata
from src.db.models.user import User


# Создаем асинхронный "движок" для подключения к БД
# pool_pre_ping=True - проверяет соединение перед использованием
# echo=False - отключает логирование SQL-запросов в stdout
engine = create_async_engine(
    DB_URL,
    echo=False,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True,
    connect_args={
        "server_settings": {
            "tcp_keepalives_idle": "60",
            "tcp_keepalives_interval": "30",
            "tcp_keepalives_count": "5",
        },
        "command_timeout": 60,
        "statement_cache_size": 0,
        "timeout": 10,
    },
)

# Создаем фабрику асинхронных сессий
async_session_factory = async_sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)


# Функция create_tables была удалена, чтобы избежать случайного изменения схемы БД.
# Для управления схемой рекомендуется использовать миграции (например, Alembic).
