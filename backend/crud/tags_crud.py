"""封装标签的数据访问函数，负责常用增删改查与查询组合。"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.tags_mod import Tag
from backend.schemas.tags_sch import TagCreate, TagUpdate


async def create_tag(db: AsyncSession, payload: TagCreate) -> Tag:
    tag = Tag(**payload.model_dump(exclude_none=True))
    db.add(tag)
    await db.commit()
    await db.refresh(tag)
    return tag


async def list_tags(db: AsyncSession) -> list[Tag]:
    result = await db.execute(select(Tag).order_by(Tag.tag_id))
    return list(result.scalars().all())


async def get_tag(db: AsyncSession, tag_id: int) -> Tag | None:
    return await db.get(Tag, tag_id)


async def update_tag(db: AsyncSession, tag: Tag, payload: TagUpdate) -> Tag:
    for field, value in payload.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(tag, field, value)
    await db.commit()
    await db.refresh(tag)
    return tag


async def delete_tag(db: AsyncSession, tag: Tag) -> None:
    await db.delete(tag)
    await db.commit()
