"""定义学习计划相关的请求体、响应体与数据校验模型。"""

from datetime import datetime

from pydantic import Field

from backend.schemas.base import ORMModel


class StudyPlanCreate(ORMModel):
    user_id: int
    plan_content: str
    execute_time: datetime | None = None
    plan_status: str = Field(default="未开始", max_length=20)


class StudyPlanUpdate(ORMModel):
    plan_content: str | None = None
    execute_time: datetime | None = None
    plan_status: str | None = Field(default=None, max_length=20)


class StudyPlanResponse(ORMModel):
    plan_id: int
    user_id: int
    plan_content: str
    execute_time: datetime | None = None
    plan_status: str
