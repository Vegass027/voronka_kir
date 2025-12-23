import secrets
import string
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# from src.config import ADMIN_TELEGRAM_ID # is_admin is removed from model
from src.db.models.user import User


class UserService:
    """Сервис для бизнес-логики, связанной с пользователями."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def _generate_unique_referral_code(self, length: int = 8) -> str:
        """Генерирует уникальный реферальный код."""
        alphabet = string.ascii_uppercase + string.digits
        while True:
            code = "".join(secrets.choice(alphabet) for _ in range(length))
            # Проверяем, что сгенерированный код уникален
            result = await self.session.execute(
                select(User).where(User.referral_code == code)
            )
            if result.scalar_one_or_none() is None:
                return code

    async def get_user_by_telegram_id(self, telegram_id: str) -> Optional[User]:
        """Находит пользователя по его Telegram ID (тип String)."""
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()
        
    async def get_user_by_referral_code(self, referral_code: str) -> Optional[User]:
        """Находит пользователя по его реферальному коду."""
        result = await self.session.execute(
            select(User).where(User.referral_code == referral_code)
        )
        return result.scalar_one_or_none()

    async def get_or_create_user(
        self,
        telegram_id: int, # Keep int as input from handler
        username: Optional[str],
        start_payload: Optional[str] = None,
        bot=None,  # Добавляем параметр для передачи бота
    ) -> User:
        """
        Получает пользователя из БД или создает нового.
        - Устанавливает реферальную связь, если был передан `start_payload`.
        """
        # 1. Пытаемся найти пользователя, telegram_id теперь строка
        user = await self.get_user_by_telegram_id(str(telegram_id))
        if user:
            # Если пользователь найден, просто возвращаем его
            return user

        # 2. Если пользователь не найден, создаем нового
        referrer = None
        if start_payload:
            # Если есть payload (реф. код), ищем пригласившего пользователя
            referrer = await self.get_user_by_referral_code(start_payload)

        # Генерируем уникальный реферальный код для нового пользователя
        new_referral_code = await self._generate_unique_referral_code()
        
        # Генерируем реферальную ссылку, если передан бот
        referral_link = None
        if bot:
            bot_username = (await bot.get_me()).username
            referral_link = f"https://t.me/{bot_username}?start={new_referral_code}"
        
        # Создаем экземпляр нового пользователя
        new_user = User(
            telegram_id=str(telegram_id), # Сохраняем как строку
            username=username,
            referral_code=new_referral_code,
            telegram_bot_referral_link=referral_link,
            referred_by_user_id=referrer.id if referrer else None,
            # is_admin был удален из модели
        )

        # Добавляем пользователя в сессию (коммит будет в middleware)
        self.session.add(new_user)
        await self.session.flush() # Чтобы получить user.id, если он нужен сразу
        
        return new_user