from pydantic import Field

from backend.schemas.base import ORMModel


class CourseCreate(ORMModel):
    course_name: str = Field(..., max_length=100)
    class_time: str | None = Field(default=None, max_length=50)
    course_intro: str | None = None


class CourseUpdate(ORMModel):
    course_name: str | None = Field(default=None, max_length=100)
    class_time: str | None = Field(default=None, max_length=50)
    course_intro: str | None = None


class CourseResponse(ORMModel):
    course_id: int
    course_name: str
    class_time: str | None = None
    course_intro: str | None = None
