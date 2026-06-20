from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.config.db_config import Base

if TYPE_CHECKING:
    from backend.models.enrollment_relations_mod import EnrollmentRelation
    from backend.models.roles_mod import Role
    from backend.models.teaching_relations_mod import TeachingRelation
    from backend.models.ai_sessions_mod import AiSession
    from backend.models.notifications_mod import Notification
    from backend.models.study_plans_mod import StudyPlan
    from backend.models.notes_mod import Note
    from backend.models.assignment_submissions_mod import AssignmentSubmission


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    gender: Mapped[str | None] = mapped_column(String(10), nullable=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.role_id"), nullable=False)

    role: Mapped["Role"] = relationship(back_populates="users")
    teaching_relations: Mapped[list["TeachingRelation"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    enrollment_relations: Mapped[list["EnrollmentRelation"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    notes: Mapped[list["Note"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    study_plans: Mapped[list["StudyPlan"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    notifications: Mapped[list["Notification"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    assignment_submissions: Mapped[list["AssignmentSubmission"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    ai_sessions: Mapped[list["AiSession"]] = relationship(back_populates="user", cascade="all, delete-orphan")
