"""定义用户相关的请求体、响应体与数据校验模型。"""

from datetime import datetime

from pydantic import Field

from backend.schemas.base import ORMModel


class UserCreate(ORMModel):
    name: str = Field(..., max_length=50)
    username: str | None = Field(default=None, max_length=50)
    password_hash: str | None = Field(default=None, max_length=255)
    gender: str | None = Field(default=None, max_length=10)
    age: int | None = Field(default=None, ge=0, le=150)
    role_id: int
    is_active: bool = True


class UserUpdate(ORMModel):
    name: str | None = Field(default=None, max_length=50)
    username: str | None = Field(default=None, max_length=50)
    password_hash: str | None = Field(default=None, max_length=255)
    gender: str | None = Field(default=None, max_length=10)
    age: int | None = Field(default=None, ge=0, le=150)
    role_id: int | None = None
    is_active: bool | None = None


class UserResponse(ORMModel):
    user_id: int
    name: str
    username: str | None = None
    gender: str | None = None
    age: int | None = None
    role_id: int
    is_active: bool = True
    created_at: datetime | None = None
