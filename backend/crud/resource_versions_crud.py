from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.resource_versions_mod import ResourceVersion
from backend.schemas.resource_versions_sch import ResourceVersionCreate, ResourceVersionUpdate


async def create_version(db: AsyncSession, payload: ResourceVersionCreate) -> ResourceVersion:
    version = ResourceVersion(**payload.model_dump(exclude_none=True))
    db.add(version)
    await db.commit()
    await db.refresh(version)
    return version


async def list_versions(db: AsyncSession, resource_id: int | None = None) -> list[ResourceVersion]:
    stmt = select(ResourceVersion)
    if resource_id is not None:
        stmt = stmt.where(ResourceVersion.resource_id == resource_id)
    result = await db.execute(stmt.order_by(ResourceVersion.version_id))
    return list(result.scalars().all())


async def get_version(db: AsyncSession, version_id: int) -> ResourceVersion | None:
    return await db.get(ResourceVersion, version_id)


async def update_version(db: AsyncSession, version: ResourceVersion, payload: ResourceVersionUpdate) -> ResourceVersion:
    for field, value in payload.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(version, field, value)
    await db.commit()
    await db.refresh(version)
    return version


async def delete_version(db: AsyncSession, version: ResourceVersion) -> None:
    await db.delete(version)
    await db.commit()
