"""定义资源标签关联相关的请求体、响应体与数据校验模型。"""

from backend.schemas.base import ORMModel


class ResourceTagCreate(ORMModel):
    resource_id: int
    tag_id: int


class ResourceTagResponse(ORMModel):
    resource_id: int
    tag_id: int
