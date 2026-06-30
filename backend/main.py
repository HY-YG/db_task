"""FastAPI 后端入口，负责初始化数据库、注册异常处理器并挂载业务路由。"""

import sys
from pathlib import Path

# 让直接执行 `python backend/main.py` 时也能正确解析到项目根包。
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from contextlib import asynccontextmanager

from fastapi import FastAPI
import uvicorn
from sqlalchemy import text

from backend.config.db_config import AsyncSessionLocal, Base, engine
from backend.routers import (
    admin,
    ai,
    auth,
    assignments,
    courses,
    learning,
    users,
)
from backend.utils.bootstrap import (
    ensure_auth_schema,
    ensure_default_admin_account,
    ensure_default_roles,
    ensure_learning_schema,
)
from backend.utils.exception_handlers import register_exception_handlers
from backend.utils.response import success_response


@asynccontextmanager
async def lifespan(_: FastAPI):
    import backend.models

    async with engine.begin() as conn:
        # AI 检索依赖 pgvector 扩展，项目启动时顺手补齐。
        await conn.execute(text("create extension if not exists vector"))
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as db:
        # 这些初始化逻辑只做“补齐”，不会覆盖已有数据。
        await ensure_auth_schema(db)
        await ensure_learning_schema(db)
        await ensure_default_roles(db)
        await ensure_default_admin_account(db)
    yield
    await engine.dispose()


app = FastAPI(title="Smart Learning Platform API", lifespan=lifespan)
register_exception_handlers(app)


@app.get("/")
async def read_root():
    return success_response({"message": "Hello, Smart Learning Platform API"})


app.include_router(users.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(courses.router, prefix="/api")
app.include_router(learning.router, prefix="/api")
app.include_router(assignments.router, prefix="/api")
app.include_router(ai.router, prefix="/api")
app.include_router(admin.router, prefix="/api")


if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
