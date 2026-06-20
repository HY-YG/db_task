from datetime import datetime

from pydantic import Field

from backend.schemas.base import ORMModel


class AssignmentSubmissionCreate(ORMModel):
    assignment_id: int
    user_id: int
    submission_status: str = Field(default="未提交", max_length=20)
    submitted_at: datetime | None = None
    submission_content: str | None = None


class AssignmentSubmissionUpdate(ORMModel):
    submission_status: str | None = Field(default=None, max_length=20)
    submitted_at: datetime | None = None
    submission_content: str | None = None


class AssignmentSubmissionResponse(ORMModel):
    submission_id: int
    assignment_id: int
    user_id: int
    submission_status: str
    submitted_at: datetime | None = None
    submission_content: str | None = None
