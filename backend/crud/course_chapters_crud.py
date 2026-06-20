from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.course_chapters_mod import CourseChapter
from backend.schemas.course_chapters_sch import CourseChapterCreate, CourseChapterUpdate


async def create_chapter(db: AsyncSession, payload: CourseChapterCreate) -> CourseChapter:
    chapter = CourseChapter(**payload.model_dump(exclude_none=True))
    db.add(chapter)
    await db.commit()
    await db.refresh(chapter)
    return chapter


async def list_chapters(db: AsyncSession, course_id: int | None = None) -> list[CourseChapter]:
    stmt = select(CourseChapter)
    if course_id is not None:
        stmt = stmt.where(CourseChapter.course_id == course_id)
    result = await db.execute(stmt.order_by(CourseChapter.course_id, CourseChapter.chapter_order))
    return list(result.scalars().all())


async def get_chapter(db: AsyncSession, chapter_id: int) -> CourseChapter | None:
    return await db.get(CourseChapter, chapter_id)


async def update_chapter(db: AsyncSession, chapter: CourseChapter, payload: CourseChapterUpdate) -> CourseChapter:
    for field, value in payload.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(chapter, field, value)
    await db.commit()
    await db.refresh(chapter)
    return chapter


async def delete_chapter(db: AsyncSession, chapter: CourseChapter) -> None:
    await db.delete(chapter)
    await db.commit()
