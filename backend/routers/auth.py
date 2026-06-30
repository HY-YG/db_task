"""提供注册、登录、登出、当前用户与密码修改等认证接口。"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config.db_config import get_db
from backend.crud import auth_crud, roles_crud
from backend.schemas.auth_sch import AuthResponse, ChangePasswordRequest, LoginRequest, RegisterRequest
from backend.schemas.users_sch import UserResponse
from backend.utils.auth import get_user_from_token
from backend.utils.response import success_response
from backend.utils.security import verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)) -> dict:
    existed = await auth_crud.get_user_by_username(db, payload.username)
    if existed is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名已存在")

    role = await roles_crud.get_role_by_name(db, payload.role_name)
    if role is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="当前角色不可注册")

    user = await auth_crud.create_user_with_password(db, payload, role.role_id)
    token_record = await auth_crud.create_token(db, user.user_id)
    return success_response(
        AuthResponse(
            token=token_record.token,
            userInfo=UserResponse.model_validate(user),
        )
    )


@router.post("/login")
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> dict:
    user = await auth_crud.authenticate_user(db, payload.username, payload.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")

    token_record = await auth_crud.create_token(db, user.user_id)
    return success_response(
        AuthResponse(
            token=token_record.token,
            userInfo=UserResponse.model_validate(user),
        )
    )


@router.get("/me")
async def get_current_user(user=Depends(get_user_from_token)) -> dict:
    return success_response(UserResponse.model_validate(user))


@router.post("/logout")
async def logout(user=Depends(get_user_from_token), db: AsyncSession = Depends(get_db)) -> dict:
    await auth_crud.delete_token_by_user_id(db, user.user_id)
    return success_response()


@router.put("/password")
async def change_password(
    payload: ChangePasswordRequest,
    user=Depends(get_user_from_token),
    db: AsyncSession = Depends(get_db),
) -> dict:
    if not verify_password(payload.old_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="旧密码不正确")
    await auth_crud.update_user_password(db, user, payload.new_password)
    return success_response(UserResponse.model_validate(user))
