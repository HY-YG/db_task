from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config.db_config import get_db
from backend.crud import roles_crud, users_crud
from backend.schemas.roles_sch import RoleCreate, RoleResponse, RoleUpdate
from backend.schemas.users_sch import UserCreate, UserResponse, UserUpdate
from backend.utils.response import success_response

router = APIRouter(tags=["users"])

roles_router = APIRouter(prefix="/roles", tags=["roles"])
users_router = APIRouter(prefix="/users", tags=["users"])


@roles_router.post("", status_code=status.HTTP_201_CREATED)
async def create_role(payload: RoleCreate, db: AsyncSession = Depends(get_db)) -> dict:
    role = await roles_crud.create_role(db, payload)
    return success_response(RoleResponse.model_validate(role))


@roles_router.get("")
async def list_roles(db: AsyncSession = Depends(get_db)) -> dict:
    roles = await roles_crud.list_roles(db)
    return success_response([RoleResponse.model_validate(item) for item in roles])


@roles_router.get("/{role_id}")
async def get_role(role_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    role = await roles_crud.get_role(db, role_id)
    if role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    return success_response(RoleResponse.model_validate(role))


@roles_router.put("/{role_id}")
async def update_role(role_id: int, payload: RoleUpdate, db: AsyncSession = Depends(get_db)) -> dict:
    role = await roles_crud.get_role(db, role_id)
    if role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    role = await roles_crud.update_role(db, role, payload)
    return success_response(RoleResponse.model_validate(role))


@roles_router.delete("/{role_id}")
async def delete_role(role_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    role = await roles_crud.get_role(db, role_id)
    if role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    await roles_crud.delete_role(db, role)
    return success_response()


@users_router.post("", status_code=status.HTTP_201_CREATED)
async def create_user(payload: UserCreate, db: AsyncSession = Depends(get_db)) -> dict:
    user = await users_crud.create_user(db, payload)
    return success_response(UserResponse.model_validate(user))


@users_router.get("")
async def list_users(db: AsyncSession = Depends(get_db)) -> dict:
    users = await users_crud.list_users(db)
    return success_response([UserResponse.model_validate(item) for item in users])


@users_router.get("/{user_id}")
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    user = await users_crud.get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return success_response(UserResponse.model_validate(user))


@users_router.put("/{user_id}")
async def update_user(user_id: int, payload: UserUpdate, db: AsyncSession = Depends(get_db)) -> dict:
    user = await users_crud.get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    user = await users_crud.update_user(db, user, payload)
    return success_response(UserResponse.model_validate(user))


@users_router.delete("/{user_id}")
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    user = await users_crud.get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    await users_crud.delete_user(db, user)
    return success_response()


router.include_router(users_router)
router.include_router(roles_router)
