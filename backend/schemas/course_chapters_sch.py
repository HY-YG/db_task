"""定义课程章节相关的请求体、响应体与数据校验模型。"""

from pydantic import Field

from backend.schemas.base import ORMModel


class CourseChapterCreate(ORMModel):
    course_id: int
    chapter_title: str = Field(..., max_length=100)
    chapter_content: str | None = None
    chapter_order: int = Field(..., ge=1)


class CourseChapterUpdate(ORMModel):
    course_id: int | None = None
    chapter_title: str | None = Field(default=None, max_length=100)
    chapter_content: str | None = None
    chapter_order: int | None = Field(default=None, ge=1)


class CourseChapterResponse(ORMModel):
    chapter_id: int
    course_id: int
    chapter_title: str
    chapter_content: str | None = None
    chapter_order: int
