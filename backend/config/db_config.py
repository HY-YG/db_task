import os
from collections.abc import AsyncGenerator
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(dotenv_path=BASE_DIR / ".env")

NEON_URL = os.getenv("NEON_URL")
if not NEON_URL:
    raise ValueError("NEON_URL 环境变量未设置！请在 .env 文件中进行配置。")

url = make_url(NEON_URL)
query = dict(url.query)
connect_args: dict[str, str] = {}

if query.pop("sslmode", None) == "require":
    connect_args["ssl"] = "require"

query.pop("channel_binding", None)

engine = create_async_engine(
    url.set(query=query).render_as_string(hide_password=False).replace("postgresql://", "postgresql+asyncpg://", 1),
    pool_pre_ping=True,
    connect_args=connect_args,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
    class_=AsyncSession,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as db:
        try:
            yield db
        except Exception:
            await db.rollback()
            raise
