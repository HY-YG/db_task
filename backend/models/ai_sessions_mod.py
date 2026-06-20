from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.config.db_config import Base

if TYPE_CHECKING:
    from backend.models.ai_messages_mod import AiMessage
    from backend.models.users_mod import User


class AiSession(Base):
    __tablename__ = "ai_sessions"

    session_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    session_status: Mapped[str] = mapped_column(String(20), nullable=False, default="进行中")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="ai_sessions")
    messages: Mapped[list["AiMessage"]] = relationship(back_populates="session", cascade="all, delete-orphan")
