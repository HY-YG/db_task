import asyncio
import sys
from pathlib import Path

from sqlalchemy import text

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.config.db_config import engine


INDEX_STATEMENTS: list[tuple[str, str]] = [
    (
        "users.role_id",
        "create index if not exists idx_users_role_id on users (role_id)",
    ),
    (
        "course_resources.chapter_id + resource_id",
        "create index if not exists idx_course_resources_chapter_resource on course_resources (chapter_id, resource_id)",
    ),
    (
        "resource_versions.resource_id + version_id",
        "create index if not exists idx_resource_versions_resource_version on resource_versions (resource_id, version_id)",
    ),
    (
        "resource_tags.tag_id + resource_id",
        "create index if not exists idx_resource_tags_tag_resource on resource_tags (tag_id, resource_id)",
    ),
    (
        "teaching_relations.course_id + user_id",
        "create index if not exists idx_teaching_relations_course_user on teaching_relations (course_id, user_id)",
    ),
    (
        "enrollment_relations.course_id + user_id",
        "create index if not exists idx_enrollment_relations_course_user on enrollment_relations (course_id, user_id)",
    ),
    (
        "study_notes.user_id + recorded_at",
        "create index if not exists idx_study_notes_user_recorded_at on study_notes (user_id, recorded_at desc)",
    ),
    (
        "study_notes.course_id + recorded_at",
        "create index if not exists idx_study_notes_course_recorded_at on study_notes (course_id, recorded_at desc)",
    ),
    (
        "study_plans.user_id + plan_id",
        "create index if not exists idx_study_plans_user_plan on study_plans (user_id, plan_id)",
    ),
    (
        "notifications.user_id + sent_at",
        "create index if not exists idx_notifications_user_sent_at on notifications (user_id, sent_at desc)",
    ),
    (
        "assignments.course_id + assignment_id",
        "create index if not exists idx_assignments_course_assignment on assignments (course_id, assignment_id)",
    ),
    (
        "assignment_submissions.assignment_id + user_id",
        "create index if not exists idx_assignment_submissions_assignment_user on assignment_submissions (assignment_id, user_id)",
    ),
    (
        "assignment_submissions.user_id + submission_id",
        "create index if not exists idx_assignment_submissions_user_submission on assignment_submissions (user_id, submission_id)",
    ),
    (
        "ai_sessions.user_id + session_id",
        "create index if not exists idx_ai_sessions_user_session on ai_sessions (user_id, session_id)",
    ),
    (
        "ai_messages.session_id + sent_at",
        "create index if not exists idx_ai_messages_session_sent_at on ai_messages (session_id, sent_at)",
    ),
    (
        "ai_messages.session_id + sender",
        "create index if not exists idx_ai_messages_session_sender on ai_messages (session_id, sender)",
    ),
    (
        "ai_messages.message_content GIN",
        "create index if not exists idx_ai_messages_message_content_gin on ai_messages using gin (message_content)",
    ),
    (
        "resource_chunks.resource_id + chunk_index",
        "create index if not exists idx_resource_chunks_resource_chunk on resource_chunks (resource_id, chunk_index)",
    ),
]


async def main() -> None:
    async with engine.begin() as conn:
        for label, sql in INDEX_STATEMENTS:
            await conn.execute(text(sql))
            print(f"OK: {label}")


if __name__ == "__main__":
    asyncio.run(main())

