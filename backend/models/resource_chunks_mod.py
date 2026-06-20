from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.config.db_config import Base

if TYPE_CHECKING:
    from backend.models.course_resources_mod import CourseResource


class ResourceChunk(Base):
    __tablename__ = "resource_chunks"

    chunk_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    resource_id: Mapped[int] = mapped_column(ForeignKey("course_resources.resource_id"), nullable=False, index=True)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    resource: Mapped["CourseResource"] = relationship()
