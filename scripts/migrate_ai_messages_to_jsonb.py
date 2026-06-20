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
        result = await conn.execute(
            text(
                """
                select udt_name
                from information_schema.columns
                where table_name = 'ai_messages' and column_name = 'message_content'
                """
            )
        )
        udt_name = result.scalar_one_or_none()
        if udt_name == "jsonb":
            print("ai_messages.message_content is already jsonb")
            return

        await conn.execute(
            text(
                """
                alter table ai_messages
                alter column message_content type jsonb
                using (
                    case
                        when message_content is null then '{}'::jsonb
                        when left(btrim(message_content), 1) in ('{', '[') then message_content::jsonb
                        else jsonb_build_object('type', 'text', 'text', message_content)
                    end
                )
                """
            )
        )
        print("migrated ai_messages.message_content to jsonb")


if __name__ == "__main__":
    asyncio.run(main())
