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
