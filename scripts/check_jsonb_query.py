import asyncio
import sys
from pathlib import Path

from sqlalchemy import text

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.config.db_config import engine


async def main() -> None:
    async with engine.begin() as conn:
        r = await conn.execute(
            text(
                """
                select
                    message_id,
                    message_content->>'type' as type,
                    message_content->>'stage' as stage
                from ai_messages
                order by message_id desc
                limit 5
                """
            )
        )
        print(r.fetchall())


if __name__ == "__main__":
    asyncio.run(main())

