import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models.user import User


class ContentService:
    """Сервис для управления персонализированным контентом."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def _get_admin_user(self, admin_id: uuid.UUID) -> Optional[User]:
        """Получает пользователя-админа по его ID."""
        return await self.session.get(User, admin_id)

    async def update_content(self, admin_id: uuid.UUID, media_type: str, file_id: str) -> None:
        """
        Обновляет file_id для указанного типа медиа у админа.
        """
        admin = await self._get_admin_user(admin_id)
        if not admin:
            # В реальном приложении здесь стоит бросать исключение или логировать ошибку
            print(f"Админ с ID {admin_id} не найден.")
            return

        # Обновляем соответствующее поле в зависимости от media_type
        if media_type == "start_video":
            admin.start_video_file_id = file_id
        elif media_type == "tourist_voice":
            admin.tourist_voice_file_id = file_id
        elif media_type == "partner_voice":
            admin.partner_voice_file_id = file_id
        else:
            # Обработка неизвестного типа медиа
            print(f"Неизвестный тип медиа: {media_type}")
            return
        
        # Добавляем изменения в сессию для последующего коммита
        self.session.add(admin)
        await self.session.flush()

    async def get_content_file_id(self, admin_id: uuid.UUID, media_type: str) -> Optional[str]:
        """
        Получает file_id для указанного типа медиа у админа.
        """
        admin = await self._get_admin_user(admin_id)
        if not admin:
            return None

        # Возвращаем file_id из соответствующего поля
        if media_type == "start_video":
            return admin.start_video_file_id
        elif media_type == "tourist_voice":
            return admin.tourist_voice_file_id
        elif media_type == "partner_voice":
            return admin.partner_voice_file_id
        
        return None
