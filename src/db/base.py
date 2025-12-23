from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import BIGINT, TIMESTAMP, Boolean, Integer, String, VARCHAR
from sqlalchemy import func

class Base(DeclarativeBase):
    """Базовая модель SQLAlchemy с общими полями."""

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now()
    )
