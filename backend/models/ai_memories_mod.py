"""定义AI 学习记忆的数据表模型、字段映射与实体关系。"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from backend.config.db_config import Base
from backend.services.embeddings import get_embedding_dimension

if TYPE_CHECKING:
    from backend.models.ai_sessions_mod import AiSession


class AiMemory(Base):
    __tablename__ = "ai_memories"

    memory_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("ai_sessions.session_id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    course_id: Mapped[int | None] = mapped_column(ForeignKey("courses.course_id"), nullable=True)
    memory_kind: Mapped[str] = mapped_column(String(40), nullable=False)
    coach_stage: Mapped[str | None] = mapped_column(String(40), nullable=True)
    summary_text: Mapped[str] = mapped_column(Text, nullable=False)
    memory_meta: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(get_embedding_dimension()), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    session: Mapped["AiSession"] = relationship()
