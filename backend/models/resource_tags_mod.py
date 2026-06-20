from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.config.db_config import Base

if TYPE_CHECKING:
    from backend.models.course_resources_mod import CourseResource
    from backend.models.tags_mod import Tag


class ResourceTag(Base):
    __tablename__ = "resource_tags"

    resource_id: Mapped[int] = mapped_column(ForeignKey("course_resources.resource_id"), primary_key=True)
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.tag_id"), primary_key=True)

    resource: Mapped["CourseResource"] = relationship(back_populates="tags")
    tag: Mapped["Tag"] = relationship(back_populates="resources")
