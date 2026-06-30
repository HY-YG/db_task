"""定义学习进度相关的请求体、响应体与数据校验模型。"""

from datetime import datetime

from pydantic import Field

from backend.schemas.base import ORMModel


class LearningProgressCreate(ORMModel):
    user_id: int
    course_id: int
    progress_type: str = Field(..., pattern="^(chapter|resource|assignment)$")
    target_id: int
    progress_status: str = Field(default="未开始", max_length=20)
    completed_at: datetime | None = None


class LearningProgressUpdate(ORMModel):
    progress_status: str | None = Field(default=None, max_length=20)
    completed_at: datetime | None = None


class LearningProgressResponse(ORMModel):
    progress_id: int
    user_id: int
    course_id: int
    progress_type: str
    target_id: int
    progress_status: str
    completed_at: datetime | None = None
    updated_at: datetime
