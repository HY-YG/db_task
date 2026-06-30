"""定义授课关系相关的请求体、响应体与数据校验模型。"""

from datetime import datetime

from backend.schemas.base import ORMModel


class TeachingRelationCreate(ORMModel):
    user_id: int
    course_id: int
    responsible_at: datetime | None = None


class TeachingRelationResponse(ORMModel):
    user_id: int
    course_id: int
    responsible_at: datetime
