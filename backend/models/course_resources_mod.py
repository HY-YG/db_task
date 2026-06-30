"""定义课程资源的数据表模型、字段映射与实体关系。"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.config.db_config import Base

if TYPE_CHECKING:
    from backend.models.course_chapters_mod import CourseChapter
    from backend.models.resource_versions_mod import ResourceVersion
    from backend.models.resource_tags_mod import ResourceTag


class CourseResource(Base):
    __tablename__ = "course_resources"

    resource_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    chapter_id: Mapped[int] = mapped_column(ForeignKey("course_chapters.chapter_id"), nullable=False)
    resource_title: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    resource_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    chapter: Mapped["CourseChapter"] = relationship(back_populates="resources")
    versions: Mapped[list["ResourceVersion"]] = relationship(back_populates="resource", cascade="all, delete-orphan")
    tags: Mapped[list["ResourceTag"]] = relationship(back_populates="resource", cascade="all, delete-orphan")
