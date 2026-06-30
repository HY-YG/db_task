"""封装资源切片的数据访问函数，负责常用增删改查与查询组合。"""

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.resource_chunks_mod import ResourceChunk
from backend.schemas.resource_chunks_sch import ResourceChunkCreate


async def upsert_chunks(db: AsyncSession, resource_id: int, chunks: list[ResourceChunkCreate]) -> list[ResourceChunk]:
    await db.execute(delete(ResourceChunk).where(ResourceChunk.resource_id == resource_id))
    items = [ResourceChunk(**chunk.model_dump()) for chunk in chunks]
    db.add_all(items)
    await db.commit()
    for item in items:
        await db.refresh(item)
    return items


async def list_chunks(db: AsyncSession, resource_id: int | None = None) -> list[ResourceChunk]:
    stmt = select(ResourceChunk)
    if resource_id is not None:
        stmt = stmt.where(ResourceChunk.resource_id == resource_id)
    result = await db.execute(stmt.order_by(ResourceChunk.resource_id, ResourceChunk.chunk_index))
    return list(result.scalars().all())
