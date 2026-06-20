from pydantic import Field

from backend.schemas.base import ORMModel


class UserCreate(ORMModel):
    name: str = Field(..., max_length=50)
    gender: str | None = Field(default=None, max_length=10)
    age: int | None = Field(default=None, ge=0, le=150)
    role_id: int


class UserUpdate(ORMModel):
    name: str | None = Field(default=None, max_length=50)
    gender: str | None = Field(default=None, max_length=10)
    age: int | None = Field(default=None, ge=0, le=150)
    role_id: int | None = None


class UserResponse(ORMModel):
    user_id: int
    name: str
    gender: str | None = None
    age: int | None = None
    role_id: int
