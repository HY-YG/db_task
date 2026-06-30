"""定义用户的数据表模型、字段映射与实体关系。"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.config.db_config import Base

if TYPE_CHECKING:
    from backend.models.ai_sessions_mod import AiSession
    from backend.models.assignment_submissions_mod import AssignmentSubmission
    from backend.models.enrollment_relations_mod import EnrollmentRelation
    from backend.models.notifications_mod import Notification
    from backend.models.notes_mod import Note
    from backend.models.roles_mod import Role
    from backend.models.study_plans_mod import StudyPlan
    from backend.models.teaching_relations_mod import TeachingRelation


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_username", "username", unique=True),
    )

    user_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    username: Mapped[str | None] = mapped_column(String(50), nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    gender: Mapped[str | None] = mapped_column(String(10), nullable=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.role_id"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    role: Mapped["Role"] = relationship(back_populates="users")
    auth_token: Mapped["UserToken | None"] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )
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


class UserToken(Base):
    __tablename__ = "user_tokens"
    __table_args__ = (
        Index("ix_user_tokens_token", "token", unique=True),
    )

    token_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False, unique=True)
    token: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user: Mapped["User"] = relationship(back_populates="auth_token")
