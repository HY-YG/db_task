"""定义选课关系的数据表模型、字段映射与实体关系。"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.config.db_config import Base

if TYPE_CHECKING:
    from backend.models.courses_mod import Course
    from backend.models.users_mod import User


class EnrollmentRelation(Base):
    __tablename__ = "enrollment_relations"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.course_id"), primary_key=True)
    enrolled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    enrollment_status: Mapped[str] = mapped_column(String(20), nullable=False, default="已选课")

    user: Mapped["User"] = relationship(back_populates="enrollment_relations")
    course: Mapped["Course"] = relationship(back_populates="enrollment_relations")
