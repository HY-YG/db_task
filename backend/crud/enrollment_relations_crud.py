"""封装选课关系的数据访问函数，负责常用增删改查与查询组合。"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.enrollment_relations_mod import EnrollmentRelation
from backend.schemas.enrollment_relations_sch import EnrollmentRelationCreate


async def create_enrollment_relation(db: AsyncSession, payload: EnrollmentRelationCreate) -> EnrollmentRelation:
    relation = EnrollmentRelation(**payload.model_dump(exclude_none=True))
    db.add(relation)
    await db.commit()
    await db.refresh(relation)
    return relation


async def list_enrollment_relations(
    db: AsyncSession,
    *,
    user_id: int | None = None,
    course_id: int | None = None,
) -> list[EnrollmentRelation]:
    stmt = select(EnrollmentRelation)
    if user_id is not None:
        stmt = stmt.where(EnrollmentRelation.user_id == user_id)
    if course_id is not None:
        stmt = stmt.where(EnrollmentRelation.course_id == course_id)
    result = await db.execute(stmt.order_by(EnrollmentRelation.user_id, EnrollmentRelation.course_id))
    return list(result.scalars().all())
