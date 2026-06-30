"""定义AI 消息的数据表模型、字段映射与实体关系。"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.config.db_config import Base

if TYPE_CHECKING:
    from backend.models.ai_sessions_mod import AiSession


class AiMessage(Base):
    __tablename__ = "ai_messages"

    message_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("ai_sessions.session_id"), nullable=False)
    sender: Mapped[str] = mapped_column(String(20), nullable=False)
    # message_content: Mapped[dict] = mapped_column(JSON().with_variant(JSONB, "postgresql"), nullable=False)
    message_content: Mapped[dict] = mapped_column(JSONB, nullable=False)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    session: Mapped["AiSession"] = relationship(back_populates="messages")
