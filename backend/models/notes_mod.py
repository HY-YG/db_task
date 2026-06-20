from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.config.db_config import Base

if TYPE_CHECKING:
    from backend.models.courses_mod import Course
    from backend.models.users_mod import User


class Note(Base):
    __tablename__ = "study_notes"

    note_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.course_id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="notes")
    course: Mapped["Course"] = relationship(back_populates="notes")
