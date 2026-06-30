"""提供学习进度、笔记、学习计划与通知等学习域接口。"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config.db_config import get_db
from backend.crud import (
    course_resources_crud,
    courses_crud,
    enrollment_relations_crud,
    learning_progress_crud,
    notifications_crud,
    notes_crud,
    study_plans_crud,
    users_crud,
)
from backend.schemas.learning_progress_sch import (
    LearningProgressCreate,
    LearningProgressResponse,
    LearningProgressUpdate,
)
from backend.schemas.notifications_sch import (
    CourseNotificationBatchDeleteRequest,
    CourseNotificationPublishRequest,
    NotificationCreate,
    NotificationResponse,
    SentCourseNotificationResponse,
    NotificationUpdate,
)
from backend.schemas.notes_sch import NoteCreate, NoteResponse, NoteUpdate
from backend.schemas.study_plans_sch import StudyPlanCreate, StudyPlanResponse, StudyPlanUpdate
from backend.utils.response import success_response

router = APIRouter(prefix="/learning", tags=["learning"])


def build_course_notification_prefix(course_name: str, sender_name: str) -> str:
    return f"【课程通知】{course_name}\n发布人：{sender_name}"


def build_course_notification_content(course_name: str, sender_name: str, content: str) -> str:
    return f"{build_course_notification_prefix(course_name, sender_name)}\n内容：{content}"


@router.post("/note/add")
async def create_note(payload: NoteCreate, db: AsyncSession = Depends(get_db)) -> dict:
    note = await notes_crud.create_note(db, payload)
    return success_response(NoteResponse.model_validate(note))


@router.get("/note/list")
async def list_notes(
    user_id: int | None = Query(default=None),
    course_id: int | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> dict:
    notes = await notes_crud.list_notes(db, user_id=user_id, course_id=course_id)
    return success_response([NoteResponse.model_validate(item) for item in notes])


@router.get("/note/detail/{note_id}")
async def get_note(note_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    note = await notes_crud.get_note(db, note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    return success_response(NoteResponse.model_validate(note))


@router.put("/note/update/{note_id}")
async def update_note(note_id: int, payload: NoteUpdate, db: AsyncSession = Depends(get_db)) -> dict:
    note = await notes_crud.get_note(db, note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    note = await notes_crud.update_note(db, note, payload)
    return success_response(NoteResponse.model_validate(note))


@router.delete("/note/delete/{note_id}")
async def delete_note(note_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    note = await notes_crud.get_note(db, note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    await notes_crud.delete_note(db, note)
    return success_response()


@router.post("/plan/add")
async def create_plan(payload: StudyPlanCreate, db: AsyncSession = Depends(get_db)) -> dict:
    plan = await study_plans_crud.create_plan(db, payload)
    return success_response(StudyPlanResponse.model_validate(plan))


@router.get("/plan/list")
async def list_plans(
    user_id: int | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> dict:
    plans = await study_plans_crud.list_plans(db, user_id=user_id)
    return success_response([StudyPlanResponse.model_validate(item) for item in plans])


@router.get("/plan/detail/{plan_id}")
async def get_plan(plan_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    plan = await study_plans_crud.get_plan(db, plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Study plan not found")
    return success_response(StudyPlanResponse.model_validate(plan))


@router.put("/plan/update/{plan_id}")
async def update_plan(plan_id: int, payload: StudyPlanUpdate, db: AsyncSession = Depends(get_db)) -> dict:
    plan = await study_plans_crud.get_plan(db, plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Study plan not found")
    plan = await study_plans_crud.update_plan(db, plan, payload)
    return success_response(StudyPlanResponse.model_validate(plan))


@router.delete("/plan/delete/{plan_id}")
async def delete_plan(plan_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    plan = await study_plans_crud.get_plan(db, plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Study plan not found")
    await study_plans_crud.delete_plan(db, plan)
    return success_response()


@router.post("/notification/add")
async def create_notification(payload: NotificationCreate, db: AsyncSession = Depends(get_db)) -> dict:
    notification = await notifications_crud.create_notification(db, payload)
    return success_response(NotificationResponse.model_validate(notification))


@router.post("/notification/publish-course")
async def publish_course_notification(
    payload: CourseNotificationPublishRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    course = await courses_crud.get_course(db, payload.course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    sender = await users_crud.get_user(db, payload.sender_user_id)
    if sender is None:
        raise HTTPException(status_code=404, detail="Sender not found")

    # 课程通知会按选课学生展开成多条站内消息，方便学生侧独立标记已读或删除。
    enrollments = await enrollment_relations_crud.list_enrollment_relations(db, course_id=payload.course_id)
    notification_content = build_course_notification_content(course.course_name, sender.name, payload.notification_content)
    notices = [
        NotificationCreate(
            user_id=item.user_id,
            notification_content=notification_content,
            is_read=False,
        )
        for item in enrollments
    ]
    created = await notifications_crud.create_notifications(db, notices) if notices else []
    return success_response(
        {
            "course_id": payload.course_id,
            "sent_count": len(created),
            "notification_content": notification_content,
        }
    )


@router.get("/notification/sent-course")
async def list_sent_course_notifications(
    sender_user_id: int = Query(...),
    course_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
) -> dict:
    course = await courses_crud.get_course(db, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    sender = await users_crud.get_user(db, sender_user_id)
    if sender is None:
        raise HTTPException(status_code=404, detail="Sender not found")

    prefix = build_course_notification_prefix(course.course_name, sender.name)
    notifications = await notifications_crud.list_notifications_by_prefix(db, prefix)
    grouped: dict[str, dict] = {}
    for item in notifications:
        # 同一内容会给每个学生各发一条，这里按内容聚合回“教师发送记录”的视图。
        bucket = grouped.get(item.notification_content)
        if bucket is None:
            grouped[item.notification_content] = {
                "notification_content": item.notification_content,
                "sent_at": item.sent_at,
                "recipient_count": 1,
            }
            continue
        bucket["recipient_count"] += 1
        if item.sent_at > bucket["sent_at"]:
            bucket["sent_at"] = item.sent_at

    payload = [
        SentCourseNotificationResponse(**item)
        for item in sorted(grouped.values(), key=lambda value: value["sent_at"], reverse=True)
    ]
    return success_response(payload)


@router.get("/notification/list")
async def list_notifications(
    user_id: int | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> dict:
    notifications = await notifications_crud.list_notifications(db, user_id=user_id)
    return success_response([NotificationResponse.model_validate(item) for item in notifications])


@router.get("/notification/detail/{notification_id}")
async def get_notification(notification_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    notification = await notifications_crud.get_notification(db, notification_id)
    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    return success_response(NotificationResponse.model_validate(notification))


@router.put("/notification/update/{notification_id}")
async def update_notification(notification_id: int, payload: NotificationUpdate, db: AsyncSession = Depends(get_db)) -> dict:
    notification = await notifications_crud.get_notification(db, notification_id)
    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    notification = await notifications_crud.update_notification(db, notification, payload)
    return success_response(NotificationResponse.model_validate(notification))


@router.delete("/notification/delete/{notification_id}")
async def delete_notification(notification_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    notification = await notifications_crud.get_notification(db, notification_id)
    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    await notifications_crud.delete_notification(db, notification)
    return success_response()


@router.post("/notification/delete-course-batch")
async def delete_course_notification_batch(
    payload: CourseNotificationBatchDeleteRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    course = await courses_crud.get_course(db, payload.course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    sender = await users_crud.get_user(db, payload.sender_user_id)
    if sender is None:
        raise HTTPException(status_code=404, detail="Sender not found")

    expected_prefix = build_course_notification_prefix(course.course_name, sender.name)
    if not payload.notification_content.startswith(expected_prefix):
        raise HTTPException(status_code=400, detail="通知内容与课程或发布人不匹配")

    deleted_count = await notifications_crud.delete_notifications_by_content(db, payload.notification_content)
    return success_response({"deleted_count": deleted_count})


@router.post("/progress/upsert")
async def upsert_progress(payload: LearningProgressCreate, db: AsyncSession = Depends(get_db)) -> dict:
    progress = await learning_progress_crud.upsert_progress(db, payload)
    if payload.progress_type == "resource":
        resource = await course_resources_crud.get_resource(db, payload.target_id)
        if resource is not None:
            chapter_resources = await course_resources_crud.list_resources(db, chapter_id=resource.chapter_id)
            resource_ids = [item.resource_id for item in chapter_resources]
            if resource_ids:
                # 资源全部完成后自动把对应章节置为完成，减少学生逐项手动同步的成本。
                resource_progress = await learning_progress_crud.list_progress(
                    db,
                    user_id=payload.user_id,
                    course_id=payload.course_id,
                    progress_type="resource",
                )
                completed_resource_ids = {
                    item.target_id
                    for item in resource_progress
                    if item.progress_status == "已完成" and item.target_id in resource_ids
                }
                chapter_status = "已完成" if len(completed_resource_ids) == len(resource_ids) else "未开始"
                await learning_progress_crud.upsert_progress(
                    db,
                    LearningProgressCreate(
                        user_id=payload.user_id,
                        course_id=payload.course_id,
                        progress_type="chapter",
                        target_id=resource.chapter_id,
                        progress_status=chapter_status,
                    ),
                )
    return success_response(LearningProgressResponse.model_validate(progress))


@router.get("/progress/list")
async def list_progress(
    user_id: int | None = Query(default=None),
    course_id: int | None = Query(default=None),
    progress_type: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> dict:
    items = await learning_progress_crud.list_progress(
        db,
        user_id=user_id,
        course_id=course_id,
        progress_type=progress_type,
    )
    return success_response([LearningProgressResponse.model_validate(item) for item in items])


@router.put("/progress/update/{progress_id}")
async def update_progress(
    progress_id: int,
    payload: LearningProgressUpdate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    progress = await learning_progress_crud.get_progress(db, progress_id)
    if progress is None:
        raise HTTPException(status_code=404, detail="Learning progress not found")
    progress = await learning_progress_crud.update_progress(db, progress, payload)
    return success_response(LearningProgressResponse.model_validate(progress))
