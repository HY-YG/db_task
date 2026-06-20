from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.teaching_relations_mod import TeachingRelation
from backend.schemas.teaching_relations_sch import TeachingRelationCreate


async def create_teaching_relation(db: AsyncSession, payload: TeachingRelationCreate) -> TeachingRelation:
    relation = TeachingRelation(**payload.model_dump(exclude_none=True))
    db.add(relation)
    await db.commit()
    await db.refresh(relation)
    return relation


async def list_teaching_relations(db: AsyncSession) -> list[TeachingRelation]:
    result = await db.execute(select(TeachingRelation).order_by(TeachingRelation.user_id, TeachingRelation.course_id))
    return list(result.scalars().all())
