from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.study_plans_mod import StudyPlan
from backend.schemas.study_plans_sch import StudyPlanCreate, StudyPlanUpdate


async def create_plan(db: AsyncSession, payload: StudyPlanCreate) -> StudyPlan:
    plan = StudyPlan(**payload.model_dump(exclude_none=True)) #转字典
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return plan


async def list_plans(db: AsyncSession, user_id: int | None = None) -> list[StudyPlan]:
    stmt = select(StudyPlan)
    if user_id is not None:
        stmt = stmt.where(StudyPlan.user_id == user_id)
    result = await db.execute(stmt.order_by(StudyPlan.plan_id))
    return list(result.scalars().all())


async def get_plan(db: AsyncSession, plan_id: int) -> StudyPlan | None:
    return await db.get(StudyPlan, plan_id)


async def update_plan(db: AsyncSession, plan: StudyPlan, payload: StudyPlanUpdate) -> StudyPlan:
    for field, value in payload.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(plan, field, value)
    await db.commit()
    await db.refresh(plan)
    return plan


async def delete_plan(db: AsyncSession, plan: StudyPlan) -> None:
    await db.delete(plan)
    await db.commit()
