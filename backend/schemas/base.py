"""定义通用 Pydantic 基类与接口响应复用结构。"""

from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
