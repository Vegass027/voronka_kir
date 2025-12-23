from __future__ import annotations
import uuid
from typing import List, Optional

from sqlalchemy import ForeignKey, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base


class User(Base):
    """Модель пользователя, адаптированная под существующую схему БД."""

    __tablename__ = "users"

    # Первичный ключ в БД - UUID
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )

    # telegram_id в БД имеет тип text, поэтому используем String
    telegram_id: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    
    username: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    # referral_code в БД - text и может быть null
    referral_code: Mapped[Optional[str]] = mapped_column(
        String, unique=True, index=True, nullable=True
    )
    
    # telegram_bot_referral_link в БД - text и может быть null
    telegram_bot_referral_link: Mapped[Optional[str]] = mapped_column(
        String, unique=True, index=True, nullable=True
    )
    
    # Внешний ключ referred_by_user_id также должен быть UUID
    referred_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )

    # Поле is_admin отсутствует в БД, поэтому убрано из модели
    
    # Связи должны использовать новый тип ключа
    referrer: Mapped[Optional["User"]] = relationship(
        "User", back_populates="referrals", remote_side=[id]
    )
    referrals: Mapped[List["User"]] = relationship("User", back_populates="referrer")

    subscription_status: Mapped[Optional[str]] = mapped_column(String, server_default='FREE')
    status: Mapped[Optional[str]] = mapped_column(String, server_default='USER')

    # --- Персонализированный контент (для админов) ---
    # Эти поля были добавлены в БД как TEXT, что соответствует String
    start_video_file_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    tourist_voice_file_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    partner_voice_file_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    def __repr__(self) -> str:
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, username='{self.username}')>"