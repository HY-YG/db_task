"""提供 AI 助手可调用的后端工具函数，用于查询学习数据与结构化信息。"""

from sqlalchemy.ext.asyncio import AsyncSession

from backend.crud import (
    ai_memories_crud,
    assignment_submissions_crud,
    assignments_crud,
    course_chapters_crud,
    course_resources_crud,
    notes_crud,
    study_plans_crud,
)
from backend.schemas.ai_sch import AiMemoryResponse
from backend.schemas.assignment_submissions_sch import AssignmentSubmissionResponse
from backend.schemas.assignments_sch import AssignmentResponse
from backend.schemas.course_chapters_sch import CourseChapterResponse
from backend.schemas.course_resources_sch import CourseResourceResponse
from backend.schemas.notes_sch import NoteResponse
from backend.schemas.study_plans_sch import StudyPlanResponse


async def query_user_notes(db: AsyncSession, user_id: int, course_id: int | None = None) -> dict:
    notes = await notes_crud.list_notes(db, user_id=user_id, course_id=course_id)
    return {"notes": [NoteResponse.model_validate(item).model_dump(mode="json") for item in notes]}


async def query_course_resources(db: AsyncSession, course_id: int) -> dict:
    chapters = await course_chapters_crud.list_chapters(db, course_id=course_id)
    chapter_models = [CourseChapterResponse.model_validate(item) for item in chapters]
    data = []
    for ch in chapter_models:
        # 这里按章节重新拼装资源树，供 AI 工具直接消费，避免模型自己再理解扁平列表关系。
        resources = await course_resources_crud.list_resources(db, chapter_id=ch.chapter_id)
        data.append(
            {
                "chapter": ch.model_dump(mode="json"),
                "resources": [CourseResourceResponse.model_validate(r).model_dump(mode="json") for r in resources],
            }
        )
    return {"course_id": course_id, "chapters": data}


async def query_assignment_status(db: AsyncSession, user_id: int, course_id: int) -> dict:
    assignments = await assignments_crud.list_assignments(db, course_id=course_id)
    assignment_models = [AssignmentResponse.model_validate(item) for item in assignments]

    submissions = await assignment_submissions_crud.list_submissions(db, user_id=user_id)
    submission_models = [AssignmentSubmissionResponse.model_validate(item) for item in submissions]
    submitted_assignment_ids = {s.assignment_id for s in submission_models}

    status = []
    for a in assignment_models:
        # AI 更关心“是否已提交”这种结论，因此这里先把提交状态做成结构化布尔值。
        status.append(
            {
                "assignment": a.model_dump(mode="json"),
                "submitted": a.assignment_id in submitted_assignment_ids,
            }
        )
    return {"course_id": course_id, "user_id": user_id, "assignments": status}


async def query_study_plans(db: AsyncSession, user_id: int, limit: int = 5) -> dict:
    plans = await study_plans_crud.list_plans(db, user_id=user_id)
    plan_models = [StudyPlanResponse.model_validate(item) for item in plans]
    recent_plans = [item.model_dump(mode="json") for item in plan_models[-limit:]]
    return {"user_id": user_id, "plans": recent_plans}


async def query_learning_memories(
    db: AsyncSession,
    user_id: int,
    course_id: int | None = None,
    memory_kind: str | None = None,
    coach_stage: str | None = None,
    topic: str | None = None,
    limit: int = 5,
) -> dict:
    memories = await ai_memories_crud.list_memories(
        db,
        user_id=user_id,
        course_id=course_id,
        memory_kind=memory_kind,
        coach_stage=coach_stage,
        topic=topic,
        limit=limit,
    )
    memory_models = [AiMemoryResponse.model_validate(item) for item in memories]
    return {
        "user_id": user_id,
        "course_id": course_id,
        "memory_kind": memory_kind,
        "coach_stage": coach_stage,
        "topic": topic,
        "memories": [item.model_dump(mode="json") for item in memory_models],
    }
