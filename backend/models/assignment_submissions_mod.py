from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.config.db_config import Base

if TYPE_CHECKING:
    from backend.models.assignments_mod import Assignment
    from backend.models.users_mod import User


class AssignmentSubmission(Base):
    __tablename__ = "assignment_submissions"

    submission_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    assignment_id: Mapped[int] = mapped_column(ForeignKey("assignments.assignment_id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    submission_status: Mapped[str] = mapped_column(String(20), nullable=False, default="未提交")
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    submission_content: Mapped[str | None] = mapped_column(Text, nullable=True)

    assignment: Mapped["Assignment"] = relationship(back_populates="submissions")
    user: Mapped["User"] = relationship(back_populates="assignment_submissions")
