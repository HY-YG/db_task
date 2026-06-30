"""定义课程资源相关的请求体、响应体与数据校验模型。"""

from datetime import datetime

from pydantic import Field

from backend.schemas.base import ORMModel


class CourseResourceCreate(ORMModel):
    chapter_id: int
    resource_title: str = Field(..., max_length=100)
    resource_content: str | None = None
    resource_type: str | None = Field(default=None, max_length=30)


class CourseResourceUpdate(ORMModel):
    chapter_id: int | None = None
    resource_title: str | None = Field(default=None, max_length=100)
    resource_content: str | None = None
    resource_type: str | None = Field(default=None, max_length=30)


class CourseResourceResponse(ORMModel):
    resource_id: int
    chapter_id: int
    resource_title: str
    resource_content: str | None = None
    resource_type: str | None = None
    uploaded_at: datetime
