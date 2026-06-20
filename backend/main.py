import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from contextlib import asynccontextmanager

from fastapi import FastAPI
import uvicorn

from backend.config.db_config import Base, engine
from backend.routers import (
    admin,
    ai,
    assignments,
    courses,
    learning,
    users,
)
from backend.utils.exception_handlers import register_exception_handlers
from backend.utils.response import success_response


@asynccontextmanager
async def lifespan(_: FastAPI):
    import backend.models

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(title="Smart Learning Platform API", lifespan=lifespan)
register_exception_handlers(app)


@app.get("/")
async def read_root():
    return success_response({"message": "Hello, Smart Learning Platform API"})


app.include_router(users.router, prefix="/api")
app.include_router(courses.router, prefix="/api")
app.include_router(learning.router, prefix="/api")
app.include_router(assignments.router, prefix="/api")
app.include_router(ai.router, prefix="/api")
app.include_router(admin.router, prefix="/api")


if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
