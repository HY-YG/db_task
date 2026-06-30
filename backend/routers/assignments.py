"""提供作业、提交记录与作业看板相关接口。"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config.db_config import get_db
from backend.crud import (
    assignment_submissions_crud,
    assignments_crud,
    courses_crud,
    enrollment_relations_crud,
    learning_progress_crud,
)
from backend.schemas.assignment_submissions_sch import (
    AssignmentSubmissionCreate,
    AssignmentSubmissionResponse,
    AssignmentSubmissionUpdate,
)
from backend.schemas.assignment_views_sch import AssignmentDashboardItem, AssignmentDashboardResponse
from backend.schemas.assignments_sch import AssignmentCreate, AssignmentResponse, AssignmentUpdate
from backend.schemas.courses_sch import CourseResponse
from backend.utils.response import success_response

router = APIRouter(prefix="/assignment", tags=["assignments"])


@router.post("/add")
async def create_assignment(payload: AssignmentCreate, db: AsyncSession = Depends(get_db)) -> dict:
    assignment = await assignments_crud.create_assignment(db, payload)
    return success_response(AssignmentResponse.model_validate(assignment))


@router.get("/list")
async def list_assignments(
    course_id: int | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> dict:
    assignments = await assignments_crud.list_assignments(db, course_id=course_id)
    return success_response([AssignmentResponse.model_validate(item) for item in assignments])


@router.get("/dashboard/{user_id}")
async def get_assignment_dashboard(
    user_id: int,
    course_id: int | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> dict:
    assignments = await assignments_crud.list_assignments(db, course_id=course_id)
    submissions = await assignment_submissions_crud.list_submissions(db, user_id=user_id)
    progress_items = await learning_progress_crud.list_progress(
        db,
        user_id=user_id,
        course_id=course_id,
        progress_type="assignment",
    )
    enrollments = await enrollment_relations_crud.list_enrollment_relations(db, user_id=user_id, course_id=course_id)
    courses = await courses_crud.list_courses(db)

    # 看板接口负责把作业、课程、提交记录和进度汇总成一个前端可直接消费的结构。
    course_map = {item.course_id: item for item in courses}
    enrolled_course_ids = {item.course_id for item in enrollments}
    latest_submission_by_assignment: dict[int, object] = {}
    for submission in submissions:
        # 同一作业可能多次保存或重新提交，只保留最新一条提交记录用于展示。
        current = latest_submission_by_assignment.get(submission.assignment_id)
        if current is None or submission.submission_id > current.submission_id:
            latest_submission_by_assignment[submission.assignment_id] = submission
    progress_map = {item.target_id: item for item in progress_items if item.target_id is not None}

    items: list[AssignmentDashboardItem] = []
    for assignment in assignments:
        course = course_map.get(assignment.course_id)
        submission = latest_submission_by_assignment.get(assignment.assignment_id)
        progress = progress_map.get(assignment.assignment_id)
        items.append(
            AssignmentDashboardItem(
                assignment=AssignmentResponse.model_validate(assignment),
                course=CourseResponse.model_validate(course) if course is not None else None,
                submission=AssignmentSubmissionResponse.model_validate(submission) if submission is not None else None,
                progress_status=progress.progress_status if progress is not None else "未开始",
                is_enrolled=assignment.course_id in enrolled_course_ids,
            )
        )
    return success_response(AssignmentDashboardResponse(items=items))


@router.get("/detail/{assignment_id}")
async def get_assignment(assignment_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    assignment = await assignments_crud.get_assignment(db, assignment_id)
    if assignment is None:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return success_response(AssignmentResponse.model_validate(assignment))


@router.put("/update/{assignment_id}")
async def update_assignment(
    assignment_id: int,
    payload: AssignmentUpdate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    assignment = await assignments_crud.get_assignment(db, assignment_id)
    if assignment is None:
        raise HTTPException(status_code=404, detail="Assignment not found")
    assignment = await assignments_crud.update_assignment(db, assignment, payload)
    return success_response(AssignmentResponse.model_validate(assignment))


@router.delete("/delete/{assignment_id}")
async def delete_assignment(assignment_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    assignment = await assignments_crud.get_assignment(db, assignment_id)
    if assignment is None:
        raise HTTPException(status_code=404, detail="Assignment not found")
    await assignments_crud.delete_assignment(db, assignment)
    return success_response()


@router.post("/submission/add/{assignment_id}")
async def create_submission(
    assignment_id: int,
    payload: AssignmentSubmissionCreate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    data = payload.model_dump(exclude_none=True)
    data["assignment_id"] = assignment_id
    submission = await assignment_submissions_crud.create_submission(db, AssignmentSubmissionCreate(**data))
    return success_response(AssignmentSubmissionResponse.model_validate(submission))


@router.get("/submission/list/{assignment_id}")
async def list_submissions(
    assignment_id: int,
    user_id: int | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> dict:
    submissions = await assignment_submissions_crud.list_submissions(db, assignment_id=assignment_id, user_id=user_id)
    return success_response([AssignmentSubmissionResponse.model_validate(item) for item in submissions])


@router.put("/submission/update/{submission_id}")
async def update_submission(
    submission_id: int,
    payload: AssignmentSubmissionUpdate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    submission = await assignment_submissions_crud.get_submission(db, submission_id)
    if submission is None:
        raise HTTPException(status_code=404, detail="Submission not found")
    submission = await assignment_submissions_crud.update_submission(db, submission, payload)
    return success_response(AssignmentSubmissionResponse.model_validate(submission))


@router.delete("/submission/delete/{submission_id}")
async def delete_submission(submission_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    submission = await assignment_submissions_crud.get_submission(db, submission_id)
    if submission is None:
        raise HTTPException(status_code=404, detail="Submission not found")
    await assignment_submissions_crud.delete_submission(db, submission)
    return success_response()
