"""定义授课关系的数据表模型、字段映射与实体关系。"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.config.db_config import Base

if TYPE_CHECKING:
    from backend.models.courses_mod import Course
    from backend.models.users_mod import User


class TeachingRelation(Base):
    __tablename__ = "teaching_relations"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.course_id"), primary_key=True)
    responsible_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="teaching_relations")
    course: Mapped["Course"] = relationship(back_populates="teaching_relations")
