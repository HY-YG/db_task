import asyncio
import sys
from pathlib import Path

from sqlalchemy import text

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.config.db_config import engine


SQL = """
select
    tablename,
    indexname
from pg_indexes
where schemaname = 'public'
  and tablename in (
      'ai_messages',
      'ai_sessions',
      'assignment_submissions',
      'assignments',
      'course_resources',
      'enrollment_relations',
      'notifications',
      'resource_chunks',
      'resource_tags',
      'resource_versions',
      'study_notes',
      'study_plans',
      'teaching_relations',
      'users'
  )
order by tablename, indexname
"""


async def main() -> None:
    async with engine.begin() as conn:
        r = await conn.execute(text(SQL))
        for row in r.fetchall():
            print(row)


if __name__ == "__main__":
    asyncio.run(main())

