from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.resource_tags_mod import ResourceTag
from backend.schemas.resource_tags_sch import ResourceTagCreate


async def create_resource_tag(db: AsyncSession, payload: ResourceTagCreate) -> ResourceTag:
    resource_tag = ResourceTag(**payload.model_dump())
    db.add(resource_tag)
    await db.commit()
    await db.refresh(resource_tag)
    return resource_tag


async def list_resource_tags(db: AsyncSession, resource_id: int | None = None, tag_id: int | None = None) -> list[ResourceTag]:
    stmt = select(ResourceTag)
    if resource_id is not None:
        stmt = stmt.where(ResourceTag.resource_id == resource_id)
    if tag_id is not None:
        stmt = stmt.where(ResourceTag.tag_id == tag_id)
    result = await db.execute(stmt.order_by(ResourceTag.resource_id, ResourceTag.tag_id))
    return list(result.scalars().all())


async def delete_resource_tag(db: AsyncSession, resource_id: int, tag_id: int) -> bool:
    resource_tag = await db.get(ResourceTag, {"resource_id": resource_id, "tag_id": tag_id})
    if resource_tag is None:
        return False
    await db.delete(resource_tag)
    await db.commit()
    return True
