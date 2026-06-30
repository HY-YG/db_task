"""定义课程聚合视图相关的请求体、响应体与数据校验模型。"""

from backend.schemas.assignments_sch import AssignmentResponse
from backend.schemas.base import ORMModel
from backend.schemas.course_chapters_sch import CourseChapterResponse
from backend.schemas.course_resources_sch import CourseResourceResponse
from backend.schemas.courses_sch import CourseResponse
from backend.schemas.enrollment_relations_sch import EnrollmentRelationResponse
from backend.schemas.learning_progress_sch import LearningProgressResponse
from backend.schemas.notes_sch import NoteResponse


class CourseOverviewItem(ORMModel):
    course: CourseResponse
    chapter_count: int
    resource_count: int
    assignment_count: int
    progress_percent: float
    is_enrolled: bool
    enrollment_status: str | None = None


class CourseOverviewResponse(ORMModel):
    items: list[CourseOverviewItem]


class CourseDetailBundleResponse(ORMModel):
    course: CourseResponse
    enrollment: EnrollmentRelationResponse | None = None
    chapters: list[CourseChapterResponse]
    resources: list[CourseResourceResponse]
    assignments: list[AssignmentResponse]
    notes: list[NoteResponse]
    progress_items: list[LearningProgressResponse]


class CourseManagementBundleResponse(ORMModel):
    courses: list[CourseResponse]
    chapters: list[CourseChapterResponse]
    resources: list[CourseResourceResponse]
