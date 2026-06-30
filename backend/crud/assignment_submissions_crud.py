"""封装作业提交的数据访问函数，负责常用增删改查与查询组合。"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.assignment_submissions_mod import AssignmentSubmission
from backend.schemas.assignment_submissions_sch import AssignmentSubmissionCreate, AssignmentSubmissionUpdate


async def create_submission(db: AsyncSession, payload: AssignmentSubmissionCreate) -> AssignmentSubmission:
    submission = AssignmentSubmission(**payload.model_dump(exclude_none=True))
    db.add(submission)
    await db.commit()
    await db.refresh(submission)
    return submission


async def list_submissions(db: AsyncSession, assignment_id: int | None = None, user_id: int | None = None) -> list[AssignmentSubmission]:
    stmt = select(AssignmentSubmission)
    if assignment_id is not None:
        stmt = stmt.where(AssignmentSubmission.assignment_id == assignment_id)
    if user_id is not None:
        stmt = stmt.where(AssignmentSubmission.user_id == user_id)
    result = await db.execute(stmt.order_by(AssignmentSubmission.submission_id))
    return list(result.scalars().all())


async def get_submission(db: AsyncSession, submission_id: int) -> AssignmentSubmission | None:
    return await db.get(AssignmentSubmission, submission_id)


async def update_submission(
    db: AsyncSession,
    submission: AssignmentSubmission,
    payload: AssignmentSubmissionUpdate,
) -> AssignmentSubmission:
    for field, value in payload.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(submission, field, value)
    await db.commit()
    await db.refresh(submission)
    return submission


async def delete_submission(db: AsyncSession, submission: AssignmentSubmission) -> None:
    await db.delete(submission)
    await db.commit()
