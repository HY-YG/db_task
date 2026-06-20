from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config.db_config import get_db
from backend.crud import assignment_submissions_crud, assignments_crud
from backend.schemas.assignment_submissions_sch import (
    AssignmentSubmissionCreate,
    AssignmentSubmissionResponse,
    AssignmentSubmissionUpdate,
)
from backend.schemas.assignments_sch import AssignmentCreate, AssignmentResponse, AssignmentUpdate
from backend.utils.response import success_response

router = APIRouter(prefix="/assignments", tags=["assignments"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_assignment(payload: AssignmentCreate, db: AsyncSession = Depends(get_db)) -> dict:
    assignment = await assignments_crud.create_assignment(db, payload)
    return success_response(AssignmentResponse.model_validate(assignment))


@router.get("")
async def list_assignments(
    course_id: int | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> dict:
    assignments = await assignments_crud.list_assignments(db, course_id=course_id)
    return success_response([AssignmentResponse.model_validate(item) for item in assignments])


@router.get("/{assignment_id}")
async def get_assignment(assignment_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    assignment = await assignments_crud.get_assignment(db, assignment_id)
    if assignment is None:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return success_response(AssignmentResponse.model_validate(assignment))


@router.put("/{assignment_id}")
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


@router.delete("/{assignment_id}")
async def delete_assignment(assignment_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    assignment = await assignments_crud.get_assignment(db, assignment_id)
    if assignment is None:
        raise HTTPException(status_code=404, detail="Assignment not found")
    await assignments_crud.delete_assignment(db, assignment)
    return success_response()


@router.post("/{assignment_id}/submissions", status_code=status.HTTP_201_CREATED)
async def create_submission(
    assignment_id: int,
    payload: AssignmentSubmissionCreate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    data = payload.model_dump(exclude_none=True)
    data["assignment_id"] = assignment_id
    submission = await assignment_submissions_crud.create_submission(db, AssignmentSubmissionCreate(**data))
    return success_response(AssignmentSubmissionResponse.model_validate(submission))


@router.get("/{assignment_id}/submissions")
async def list_submissions(
    assignment_id: int,
    user_id: int | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> dict:
    submissions = await assignment_submissions_crud.list_submissions(db, assignment_id=assignment_id, user_id=user_id)
    return success_response([AssignmentSubmissionResponse.model_validate(item) for item in submissions])


@router.put("/submissions/{submission_id}")
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


@router.delete("/submissions/{submission_id}")
async def delete_submission(submission_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    submission = await assignment_submissions_crud.get_submission(db, submission_id)
    if submission is None:
        raise HTTPException(status_code=404, detail="Submission not found")
    await assignment_submissions_crud.delete_submission(db, submission)
    return success_response()
