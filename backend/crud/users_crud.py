from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.users_mod import User
from backend.schemas.users_sch import UserCreate, UserUpdate


async def create_user(db: AsyncSession, payload: UserCreate) -> User:
    user = User(**payload.model_dump(exclude_none=True))
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def list_users(db: AsyncSession) -> list[User]:
    result = await db.execute(select(User).order_by(User.user_id))
    return list(result.scalars().all())


async def get_user(db: AsyncSession, user_id: int) -> User | None:
    return await db.get(User, user_id)


async def update_user(db: AsyncSession, user: User, payload: UserUpdate) -> User:
    for field, value in payload.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(user, field, value)
    await db.commit()
    await db.refresh(user)
    return user


async def delete_user(db: AsyncSession, user: User) -> None:
    await db.delete(user)
    await db.commit()
