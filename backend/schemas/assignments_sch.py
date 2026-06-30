"""定义作业相关的请求体、响应体与数据校验模型。"""

from datetime import datetime

from backend.schemas.base import ORMModel


class AssignmentCreate(ORMModel):
    course_id: int
    assignment_content: str
    due_at: datetime | None = None


class AssignmentUpdate(ORMModel):
    assignment_content: str | None = None
    due_at: datetime | None = None


class AssignmentResponse(ORMModel):
    assignment_id: int
    course_id: int
    assignment_content: str
    due_at: datetime | None = None
    published_at: datetime
