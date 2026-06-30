"""定义资源版本相关的请求体、响应体与数据校验模型。"""

from datetime import datetime

from pydantic import Field

from backend.schemas.base import ORMModel


class ResourceVersionCreate(ORMModel):
    resource_id: int
    version_status: str | None = Field(default=None, max_length=20)
    version_description: str | None = None


class ResourceVersionUpdate(ORMModel):
    version_status: str | None = Field(default=None, max_length=20)
    version_description: str | None = None


class ResourceVersionResponse(ORMModel):
    version_id: int
    resource_id: int
    version_status: str | None = None
    updated_at: datetime
    version_description: str | None = None
