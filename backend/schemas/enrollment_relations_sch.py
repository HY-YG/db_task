"""定义选课关系相关的请求体、响应体与数据校验模型。"""

from datetime import datetime

from pydantic import Field

from backend.schemas.base import ORMModel


class EnrollmentRelationCreate(ORMModel):
    user_id: int
    course_id: int
    enrolled_at: datetime | None = None
    enrollment_status: str = Field(default="已选课", max_length=20)


class EnrollmentRelationResponse(ORMModel):
    user_id: int
    course_id: int
    enrolled_at: datetime
    enrollment_status: str
