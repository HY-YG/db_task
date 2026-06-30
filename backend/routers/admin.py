"""提供管理员侧接口，处理用户管理、角色权限等后台操作。"""

from fastapi import APIRouter

from backend.utils.response import success_response

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/health")
async def health() -> dict:
    return success_response({"status": "ok"})
