from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.config.db_config import Base

if TYPE_CHECKING:
    from backend.models.course_resources_mod import CourseResource


class ResourceVersion(Base):
    __tablename__ = "resource_versions"

    version_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    resource_id: Mapped[int] = mapped_column(ForeignKey("course_resources.resource_id"), nullable=False)
    version_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    version_description: Mapped[str | None] = mapped_column(Text, nullable=True)

    resource: Mapped["CourseResource"] = relationship(back_populates="versions")
