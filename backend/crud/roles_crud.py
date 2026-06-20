from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.roles_mod import Role
from backend.schemas.roles_sch import RoleCreate, RoleUpdate


async def create_role(db: AsyncSession, payload: RoleCreate) -> Role:
    role = Role(**payload.model_dump(exclude_none=True))
    db.add(role)
    await db.commit()
    await db.refresh(role)
    return role


async def list_roles(db: AsyncSession) -> list[Role]:
    result = await db.execute(select(Role).order_by(Role.role_id))
    return list(result.scalars().all())


async def get_role(db: AsyncSession, role_id: int) -> Role | None:
    return await db.get(Role, role_id)


async def update_role(db: AsyncSession, role: Role, payload: RoleUpdate) -> Role:
    for field, value in payload.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(role, field, value)
    await db.commit()
    await db.refresh(role)
    return role


async def delete_role(db: AsyncSession, role: Role) -> None:
    await db.delete(role)
    await db.commit()
