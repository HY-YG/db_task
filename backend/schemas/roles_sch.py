from pydantic import Field

from backend.schemas.base import ORMModel


class RoleCreate(ORMModel):
    role_name: str = Field(..., max_length=20)
    permission_description: str | None = None


class RoleUpdate(ORMModel):
    role_name: str | None = Field(default=None, max_length=20)
    permission_description: str | None = None


class RoleResponse(ORMModel):
    role_id: int
    role_name: str
    permission_description: str | None = None
