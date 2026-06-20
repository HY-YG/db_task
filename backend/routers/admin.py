from fastapi import APIRouter

from backend.utils.response import success_response

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/health")
async def health() -> dict:
    return success_response({"status": "ok"})
