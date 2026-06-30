"""封装授课关系的数据访问函数，负责常用增删改查与查询组合。"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.teaching_relations_mod import TeachingRelation
from backend.schemas.teaching_relations_sch import TeachingRelationCreate


async def create_teaching_relation(db: AsyncSession, payload: TeachingRelationCreate) -> TeachingRelation:
    existing = await db.get(
        TeachingRelation,
        {"user_id": payload.user_id, "course_id": payload.course_id},
    )
    if existing is not None:
        return existing
    relation = TeachingRelation(**payload.model_dump(exclude_none=True))
    db.add(relation)
    await db.commit()
    await db.refresh(relation)
    return relation


async def list_teaching_relations(db: AsyncSession, user_id: int | None = None) -> list[TeachingRelation]:
    stmt = select(TeachingRelation)
    if user_id is not None:
        stmt = stmt.where(TeachingRelation.user_id == user_id)
    result = await db.execute(stmt.order_by(TeachingRelation.user_id, TeachingRelation.course_id))
    return list(result.scalars().all())
