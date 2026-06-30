"""封装认证与登录的数据访问函数，负责常用增删改查与查询组合。"""

import uuid
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.users_mod import User, UserToken
from backend.schemas.auth_sch import RegisterRequest
from backend.schemas.users_sch import UserCreate
from backend.utils.security import get_password_hash, verify_password


async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def create_user_with_password(db: AsyncSession, payload: RegisterRequest, role_id: int) -> User:
    user = User(
        **UserCreate(
            name=payload.name,
            username=payload.username,
            password_hash=get_password_hash(payload.password),
            gender=payload.gender,
            age=payload.age,
            role_id=role_id,
            is_active=True,
        ).model_dump(exclude_none=True)
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, username: str, password: str) -> User | None:
    user = await get_user_by_username(db, username)
    if user is None or not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


async def create_token(db: AsyncSession, user_id: int) -> UserToken:
    token_value = str(uuid.uuid4())
    expires_at = datetime.now() + timedelta(days=7)
    result = await db.execute(select(UserToken).where(UserToken.user_id == user_id))
    token_record = result.scalar_one_or_none()
    if token_record is None:
        token_record = UserToken(user_id=user_id, token=token_value, expires_at=expires_at)
    else:
        token_record.token = token_value
        token_record.expires_at = expires_at
    db.add(token_record)
    await db.commit()
    await db.refresh(token_record)
    return token_record


async def get_user_by_token(db: AsyncSession, token: str) -> User | None:
    result = await db.execute(select(UserToken).where(UserToken.token == token))
    token_record = result.scalar_one_or_none()
    if token_record is None or token_record.expires_at < datetime.now():
        return None
    return await db.get(User, token_record.user_id)


async def delete_token_by_user_id(db: AsyncSession, user_id: int) -> None:
    result = await db.execute(select(UserToken).where(UserToken.user_id == user_id))
    token_record = result.scalar_one_or_none()
    if token_record is None:
        return
    await db.delete(token_record)
    await db.commit()


async def update_user_password(db: AsyncSession, user: User, new_password: str) -> User:
    user.password_hash = get_password_hash(new_password)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
