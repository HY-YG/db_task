"""封装课程资源的数据访问函数，负责常用增删改查与查询组合。"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.course_chapters_mod import CourseChapter
from backend.models.course_resources_mod import CourseResource
from backend.schemas.course_resources_sch import CourseResourceCreate, CourseResourceUpdate


async def create_resource(db: AsyncSession, payload: CourseResourceCreate) -> CourseResource:
    resource = CourseResource(**payload.model_dump(exclude_none=True))
    db.add(resource)
    await db.commit()
    await db.refresh(resource)
    return resource


async def list_resources(db: AsyncSession, chapter_id: int | None = None) -> list[CourseResource]:
    stmt = select(CourseResource)
    if chapter_id is not None:
        stmt = stmt.where(CourseResource.chapter_id == chapter_id)
    result = await db.execute(stmt.order_by(CourseResource.resource_id))
    return list(result.scalars().all())


async def list_resources_by_course(db: AsyncSession, course_id: int) -> list[CourseResource]:
    stmt = (
        select(CourseResource)
        .join(CourseChapter, CourseChapter.chapter_id == CourseResource.chapter_id)
        .where(CourseChapter.course_id == course_id)
        .order_by(CourseChapter.chapter_order, CourseResource.resource_id)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_resource(db: AsyncSession, resource_id: int) -> CourseResource | None:
    return await db.get(CourseResource, resource_id)


async def update_resource(db: AsyncSession, resource: CourseResource, payload: CourseResourceUpdate) -> CourseResource:
    for field, value in payload.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(resource, field, value)
    await db.commit()
    await db.refresh(resource)
    return resource


async def delete_resource(db: AsyncSession, resource: CourseResource) -> None:
    await db.delete(resource)
    await db.commit()
