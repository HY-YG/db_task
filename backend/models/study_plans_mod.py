"""定义学习计划的数据表模型、字段映射与实体关系。"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.config.db_config import Base

if TYPE_CHECKING:
    from backend.models.users_mod import User


class StudyPlan(Base):
    __tablename__ = "study_plans"

    plan_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    plan_content: Mapped[str] = mapped_column(Text, nullable=False)
    execute_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    plan_status: Mapped[str] = mapped_column(String(20), nullable=False, default="未开始")

    user: Mapped["User"] = relationship(back_populates="study_plans")
