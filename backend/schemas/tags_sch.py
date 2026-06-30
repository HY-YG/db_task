"""定义标签相关的请求体、响应体与数据校验模型。"""

from pydantic import Field

from backend.schemas.base import ORMModel


class TagCreate(ORMModel):
    tag_name: str = Field(..., max_length=50)
    tag_meaning: str | None = None


class TagUpdate(ORMModel):
    tag_name: str | None = Field(default=None, max_length=50)
    tag_meaning: str | None = None


class TagResponse(ORMModel):
    tag_id: int
    tag_name: str
    tag_meaning: str | None = None
