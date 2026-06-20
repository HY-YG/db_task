from typing import TYPE_CHECKING

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.config.db_config import Base

if TYPE_CHECKING:
    from backend.models.resource_tags_mod import ResourceTag


class Tag(Base):
    __tablename__ = "tags"

    tag_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tag_name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    tag_meaning: Mapped[str | None] = mapped_column(Text, nullable=True)

    resources: Mapped[list["ResourceTag"]] = relationship(back_populates="tag", cascade="all, delete-orphan")
