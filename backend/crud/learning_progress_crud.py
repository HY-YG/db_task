"""封装学习进度的数据访问函数，负责常用增删改查与查询组合。"""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.learning_progress_mod import LearningProgress
from backend.schemas.learning_progress_sch import LearningProgressCreate, LearningProgressUpdate


async def create_progress(db: AsyncSession, payload: LearningProgressCreate) -> LearningProgress:
    progress = LearningProgress(**payload.model_dump(exclude_none=True))
    db.add(progress)
    await db.commit()
    await db.refresh(progress)
    return progress


async def list_progress(
    db: AsyncSession,
    *,
    user_id: int | None = None,
    course_id: int | None = None,
    progress_type: str | None = None,
) -> list[LearningProgress]:
    stmt = select(LearningProgress)
    if user_id is not None:
        stmt = stmt.where(LearningProgress.user_id == user_id)
    if course_id is not None:
        stmt = stmt.where(LearningProgress.course_id == course_id)
    if progress_type is not None:
        stmt = stmt.where(LearningProgress.progress_type == progress_type)
    result = await db.execute(
        stmt.order_by(LearningProgress.course_id, LearningProgress.progress_type, LearningProgress.target_id)
    )
    return list(result.scalars().all())


async def get_progress(db: AsyncSession, progress_id: int) -> LearningProgress | None:
    return await db.get(LearningProgress, progress_id)


async def get_progress_by_target(
    db: AsyncSession,
    *,
    user_id: int,
    course_id: int,
    progress_type: str,
    target_id: int,
) -> LearningProgress | None:
    result = await db.execute(
        select(LearningProgress).where(
            LearningProgress.user_id == user_id,
            LearningProgress.course_id == course_id,
            LearningProgress.progress_type == progress_type,
            LearningProgress.target_id == target_id,
        )
    )
    return result.scalar_one_or_none()


async def update_progress(
    db: AsyncSession,
    progress: LearningProgress,
    payload: LearningProgressUpdate,
) -> LearningProgress:
    for field, value in payload.model_dump(exclude_unset=True, exclude_none=False).items():
        setattr(progress, field, value)
    if progress.progress_status != "已完成":
        progress.completed_at = None
    elif progress.completed_at is None:
        progress.completed_at = datetime.now()
    await db.commit()
    await db.refresh(progress)
    return progress


async def upsert_progress(db: AsyncSession, payload: LearningProgressCreate) -> LearningProgress:
    progress = await get_progress_by_target(
        db,
        user_id=payload.user_id,
        course_id=payload.course_id,
        progress_type=payload.progress_type,
        target_id=payload.target_id,
    )
    if progress is None:
        data = payload.model_dump(exclude_none=True)
        if data.get("progress_status") == "已完成" and data.get("completed_at") is None:
            data["completed_at"] = datetime.now()
        return await create_progress(db, LearningProgressCreate(**data))

    update_payload = LearningProgressUpdate(
        progress_status=payload.progress_status,
        completed_at=payload.completed_at,
    )
    return await update_progress(db, progress, update_payload)
