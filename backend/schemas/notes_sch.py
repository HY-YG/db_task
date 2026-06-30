"""定义课程笔记相关的请求体、响应体与数据校验模型。"""

from datetime import datetime

from backend.schemas.base import ORMModel


class NoteCreate(ORMModel):
    user_id: int
    course_id: int
    content: str


class NoteUpdate(ORMModel):
    content: str | None = None


class NoteResponse(ORMModel):
    note_id: int
    user_id: int
    course_id: int
    content: str
    recorded_at: datetime
