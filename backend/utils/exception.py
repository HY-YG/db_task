"""定义项目内统一使用的业务异常类型。"""

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from backend.utils.response import success_response

async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=success_response(data=None, message=str(exc.detail), code=exc.status_code),
    )


async def integrity_error_handler(_: Request, exc: IntegrityError) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content=success_response(data=None, message="Integrity error", code=409),
    )


async def sqlalchemy_error_handler(_: Request, exc: SQLAlchemyError) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content=success_response(data=None, message="Database error", code=500),
    )


async def general_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content=success_response(data=None, message="Internal server error", code=500),
    )
