from backend.models.ai_messages_mod import AiMessage
from backend.models.ai_sessions_mod import AiSession
from backend.models.assignment_submissions_mod import AssignmentSubmission
from backend.models.assignments_mod import Assignment
from backend.models.course_chapters_mod import CourseChapter
from backend.models.course_resources_mod import CourseResource
from backend.models.courses_mod import Course
from backend.models.enrollment_relations_mod import EnrollmentRelation
from backend.models.notifications_mod import Notification
from backend.models.notes_mod import Note
from backend.models.resource_chunks_mod import ResourceChunk
from backend.models.resource_tags_mod import ResourceTag
from backend.models.resource_versions_mod import ResourceVersion
from backend.models.roles_mod import Role
from backend.models.study_plans_mod import StudyPlan
from backend.models.tags_mod import Tag
from backend.models.teaching_relations_mod import TeachingRelation
from backend.models.users_mod import User

__all__ = [
    "AiMessage",
    "AiSession",
    "Assignment",
    "AssignmentSubmission",
    "Course",
    "CourseChapter",
    "CourseResource",
    "EnrollmentRelation",
    "Notification",
    "Note",
    "ResourceChunk",
    "ResourceTag",
    "ResourceVersion",
    "Role",
    "StudyPlan",
    "Tag",
    "TeachingRelation",
    "User",
]
