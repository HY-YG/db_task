"""定义学习进度的数据表模型、字段映射与实体关系。"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.config.db_config import Base


class LearningProgress(Base):
    __tablename__ = "learning_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "course_id", "progress_type", "target_id", name="uq_learning_progress_target"),
    )

    progress_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.course_id"), nullable=False)
    progress_type: Mapped[str] = mapped_column(String(20), nullable=False)
    target_id: Mapped[int] = mapped_column(Integer, nullable=False)
    progress_status: Mapped[str] = mapped_column(String(20), nullable=False, default="未开始")
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
