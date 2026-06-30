"""定义资源切片相关的请求体、响应体与数据校验模型。"""

from datetime import datetime

from pydantic import Field

from backend.schemas.base import ORMModel


class ResourceChunkCreate(ORMModel):
    resource_id: int
    chunk_index: int = Field(ge=0)
    content: str
    embedding: str


class ResourceChunkResponse(ORMModel):
    chunk_id: int
    resource_id: int
    chunk_index: int
    content: str
    embedding: str
    created_at: datetime
