from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.config.db_config import Base

if TYPE_CHECKING:
    from backend.models.courses_mod import Course
    from backend.models.course_resources_mod import CourseResource


class CourseChapter(Base):
    __tablename__ = "course_chapters"
    __table_args__ = (UniqueConstraint("course_id", "chapter_order", name="uq_course_chapter_order"),)

    chapter_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.course_id"), nullable=False)
    chapter_title: Mapped[str] = mapped_column(String(100), nullable=False)
    chapter_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    chapter_order: Mapped[int] = mapped_column(Integer, nullable=False)

    course: Mapped["Course"] = relationship(back_populates="chapters")
    resources: Mapped[list["CourseResource"]] = relationship(back_populates="chapter", cascade="all, delete-orphan")
