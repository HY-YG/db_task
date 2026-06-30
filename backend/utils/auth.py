"""封装鉴权依赖、当前用户解析与权限校验辅助逻辑。"""

from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config.db_config import get_db
from backend.crud import auth_crud
from backend.models.users_mod import User


async def get_user_from_token(
    authorization: str = Header(..., description="Bearer token"),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token format")

    token = authorization.split(" ", 1)[1]
    user = await auth_crud.get_user_by_token(db, token)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return user


async def get_current_user_optional(
    authorization: Optional[str] = Header(default=None, description="Bearer token"),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split(" ", 1)[1]
    return await auth_crud.get_user_by_token(db, token)
