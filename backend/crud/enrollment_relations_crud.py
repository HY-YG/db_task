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


async def list_enrollment_relations(db: AsyncSession) -> list[EnrollmentRelation]:
    result = await db.execute(select(EnrollmentRelation).order_by(EnrollmentRelation.user_id, EnrollmentRelation.course_id))
    return list(result.scalars().all())
