from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.courses_mod import Course
from backend.schemas.courses_sch import CourseCreate, CourseUpdate


async def create_course(db: AsyncSession, payload: CourseCreate) -> Course:
    course = Course(**payload.model_dump(exclude_none=True))
    db.add(course)
    await db.commit()
    await db.refresh(course)
    return course


async def list_courses(db: AsyncSession) -> list[Course]:
    result = await db.execute(select(Course).order_by(Course.course_id))
    return list(result.scalars().all())


async def get_course(db: AsyncSession, course_id: int) -> Course | None:
    return await db.get(Course, course_id)


async def update_course(db: AsyncSession, course: Course, payload: CourseUpdate) -> Course:
    for field, value in payload.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(course, field, value)
    await db.commit()
    await db.refresh(course)
    return course


async def delete_course(db: AsyncSession, course: Course) -> None:
    await db.delete(course)
    await db.commit()
