"""定义课程的数据表模型、字段映射与实体关系。"""

from typing import TYPE_CHECKING

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.config.db_config import Base

if TYPE_CHECKING:
    from backend.models.course_chapters_mod import CourseChapter
    from backend.models.enrollment_relations_mod import EnrollmentRelation
    from backend.models.teaching_relations_mod import TeachingRelation
    from backend.models.assignments_mod import Assignment
    from backend.models.notes_mod import Note


class Course(Base):
    __tablename__ = "courses"

    course_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    course_name: Mapped[str] = mapped_column(String(100), nullable=False)
    class_time: Mapped[str | None] = mapped_column(String(50), nullable=True)
    course_intro: Mapped[str | None] = mapped_column(Text, nullable=True)

    chapters: Mapped[list["CourseChapter"]] = relationship(back_populates="course", cascade="all, delete-orphan")
    teaching_relations: Mapped[list["TeachingRelation"]] = relationship(back_populates="course", cascade="all, delete-orphan")
    enrollment_relations: Mapped[list["EnrollmentRelation"]] = relationship(back_populates="course", cascade="all, delete-orphan")
    assignments: Mapped[list["Assignment"]] = relationship(back_populates="course", cascade="all, delete-orphan")
    notes: Mapped[list["Note"]] = relationship(back_populates="course", cascade="all, delete-orphan")
