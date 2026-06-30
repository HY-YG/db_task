"""封装作业的数据访问函数，负责常用增删改查与查询组合。"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.assignments_mod import Assignment
from backend.schemas.assignments_sch import AssignmentCreate, AssignmentUpdate


async def create_assignment(db: AsyncSession, payload: AssignmentCreate) -> Assignment:
    assignment = Assignment(**payload.model_dump(exclude_none=True))
    db.add(assignment)
    await db.commit()
    await db.refresh(assignment)
    return assignment


async def list_assignments(db: AsyncSession, course_id: int | None = None) -> list[Assignment]:
    stmt = select(Assignment)
    if course_id is not None:
        stmt = stmt.where(Assignment.course_id == course_id)
    result = await db.execute(stmt.order_by(Assignment.assignment_id))
    return list(result.scalars().all())


async def get_assignment(db: AsyncSession, assignment_id: int) -> Assignment | None:
    return await db.get(Assignment, assignment_id)


async def update_assignment(db: AsyncSession, assignment: Assignment, payload: AssignmentUpdate) -> Assignment:
    for field, value in payload.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(assignment, field, value)
    await db.commit()
    await db.refresh(assignment)
    return assignment


async def delete_assignment(db: AsyncSession, assignment: Assignment) -> None:
    await db.delete(assignment)
    await db.commit()
