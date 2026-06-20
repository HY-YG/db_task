from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config.db_config import get_db
from backend.crud import notifications_crud, notes_crud, study_plans_crud
from backend.schemas.notifications_sch import NotificationCreate, NotificationResponse, NotificationUpdate
from backend.schemas.notes_sch import NoteCreate, NoteResponse, NoteUpdate
from backend.schemas.study_plans_sch import StudyPlanCreate, StudyPlanResponse, StudyPlanUpdate
from backend.utils.response import success_response

router = APIRouter(prefix="/learning", tags=["learning"])


@router.post("/notes", status_code=status.HTTP_201_CREATED)
async def create_note(payload: NoteCreate, db: AsyncSession = Depends(get_db)) -> dict:
    note = await notes_crud.create_note(db, payload)
    return success_response(NoteResponse.model_validate(note))


@router.get("/notes")
async def list_notes(
    user_id: int | None = Query(default=None),
    course_id: int | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> dict:
    notes = await notes_crud.list_notes(db, user_id=user_id, course_id=course_id)
    return success_response([NoteResponse.model_validate(item) for item in notes])


@router.get("/notes/{note_id}")
async def get_note(note_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    note = await notes_crud.get_note(db, note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    return success_response(NoteResponse.model_validate(note))


@router.put("/notes/{note_id}")
async def update_note(note_id: int, payload: NoteUpdate, db: AsyncSession = Depends(get_db)) -> dict:
    note = await notes_crud.get_note(db, note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    note = await notes_crud.update_note(db, note, payload)
    return success_response(NoteResponse.model_validate(note))


@router.delete("/notes/{note_id}")
async def delete_note(note_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    note = await notes_crud.get_note(db, note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    await notes_crud.delete_note(db, note)
    return success_response()


@router.post("/study-plans", status_code=status.HTTP_201_CREATED)
async def create_plan(payload: StudyPlanCreate, db: AsyncSession = Depends(get_db)) -> dict:
    plan = await study_plans_crud.create_plan(db, payload)
    return success_response(StudyPlanResponse.model_validate(plan))


@router.get("/study-plans")
async def list_plans(
    user_id: int | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> dict:
    plans = await study_plans_crud.list_plans(db, user_id=user_id)
    return success_response([StudyPlanResponse.model_validate(item) for item in plans])


@router.get("/study-plans/{plan_id}")
async def get_plan(plan_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    plan = await study_plans_crud.get_plan(db, plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Study plan not found")
    return success_response(StudyPlanResponse.model_validate(plan))


@router.put("/study-plans/{plan_id}")
async def update_plan(plan_id: int, payload: StudyPlanUpdate, db: AsyncSession = Depends(get_db)) -> dict:
    plan = await study_plans_crud.get_plan(db, plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Study plan not found")
    plan = await study_plans_crud.update_plan(db, plan, payload)
    return success_response(StudyPlanResponse.model_validate(plan))


@router.delete("/study-plans/{plan_id}")
async def delete_plan(plan_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    plan = await study_plans_crud.get_plan(db, plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Study plan not found")
    await study_plans_crud.delete_plan(db, plan)
    return success_response()


@router.post("/notifications", status_code=status.HTTP_201_CREATED)
async def create_notification(payload: NotificationCreate, db: AsyncSession = Depends(get_db)) -> dict:
    notification = await notifications_crud.create_notification(db, payload)
    return success_response(NotificationResponse.model_validate(notification))


@router.get("/notifications")
async def list_notifications(
    user_id: int | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> dict:
    notifications = await notifications_crud.list_notifications(db, user_id=user_id)
    return success_response([NotificationResponse.model_validate(item) for item in notifications])


@router.get("/notifications/{notification_id}")
async def get_notification(notification_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    notification = await notifications_crud.get_notification(db, notification_id)
    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    return success_response(NotificationResponse.model_validate(notification))


@router.put("/notifications/{notification_id}")
async def update_notification(notification_id: int, payload: NotificationUpdate, db: AsyncSession = Depends(get_db)) -> dict:
    notification = await notifications_crud.get_notification(db, notification_id)
    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    notification = await notifications_crud.update_notification(db, notification, payload)
    return success_response(NotificationResponse.model_validate(notification))


@router.delete("/notifications/{notification_id}")
async def delete_notification(notification_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    notification = await notifications_crud.get_notification(db, notification_id)
    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    await notifications_crud.delete_notification(db, notification)
    return success_response()
