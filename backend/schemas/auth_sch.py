"""定义认证与登录相关的请求体、响应体与数据校验模型。"""

from pydantic import ConfigDict, Field

from backend.schemas.base import ORMModel
from backend.schemas.users_sch import UserResponse


class LoginRequest(ORMModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=50)


class RegisterRequest(ORMModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=50)
    name: str = Field(..., min_length=1, max_length=50)
    gender: str | None = Field(default=None, max_length=10)
    age: int | None = Field(default=None, ge=0, le=150)
    role_name: str = Field(..., pattern="^(学生|教师)$")


class ChangePasswordRequest(ORMModel):
    old_password: str = Field(..., min_length=6, max_length=50)
    new_password: str = Field(..., min_length=6, max_length=50)


class AuthResponse(ORMModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    token: str
    user_info: UserResponse = Field(alias="userInfo")
