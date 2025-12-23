from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class DbSessionMiddleware(BaseMiddleware):
    """
    Middleware для управления сессиями и транзакциями базы данных.

    Для каждого входящего события создается новая сессия `AsyncSession`,
    которая передается в хендлер через `data['session']`.

    - Если хендлер завершается успешно, транзакция коммитится.
    - Если в хендлере возникает исключение, транзакция откатывается.
    - Сессия автоматически закрывается после обработки.
    """

    def __init__(self, session_pool: async_sessionmaker[AsyncSession]):
        super().__init__()
        self.session_pool = session_pool

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        async with self.session_pool() as session:
            data["session"] = session
            try:
                result = await handler(event, data)
                # Явный коммит, если хендлер отработал без ошибок
                await session.commit()
                return result
            except Exception:
                # Откат транзакции при любой ошибке
                await session.rollback()
                raise
