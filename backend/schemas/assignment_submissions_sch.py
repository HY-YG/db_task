"""定义作业提交相关的请求体、响应体与数据校验模型。"""

from datetime import datetime

from pydantic import Field

from backend.schemas.base import ORMModel


class AssignmentSubmissionCreate(ORMModel):
    assignment_id: int | None = None
    user_id: int
    submission_status: str = Field(default="未提交", max_length=20)
    submitted_at: datetime | None = None
    submission_content: str | None = None
    teacher_feedback: str | None = None
    score: int | None = Field(default=None, ge=0, le=100)
    reviewed_at: datetime | None = None


class AssignmentSubmissionUpdate(ORMModel):
    submission_status: str | None = Field(default=None, max_length=20)
    submitted_at: datetime | None = None
    submission_content: str | None = None
    teacher_feedback: str | None = None
    score: int | None = Field(default=None, ge=0, le=100)
    reviewed_at: datetime | None = None


class AssignmentSubmissionResponse(ORMModel):
    submission_id: int
    assignment_id: int
    user_id: int
    submission_status: str
    submitted_at: datetime | None = None
    submission_content: str | None = None
    teacher_feedback: str | None = None
    score: int | None = None
    reviewed_at: datetime | None = None
