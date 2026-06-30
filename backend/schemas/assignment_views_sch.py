"""定义作业聚合视图相关的请求体、响应体与数据校验模型。"""

from backend.schemas.assignment_submissions_sch import AssignmentSubmissionResponse
from backend.schemas.assignments_sch import AssignmentResponse
from backend.schemas.base import ORMModel
from backend.schemas.courses_sch import CourseResponse


class AssignmentDashboardItem(ORMModel):
    assignment: AssignmentResponse
    course: CourseResponse | None = None
    submission: AssignmentSubmissionResponse | None = None
    progress_status: str = "未开始"
    is_enrolled: bool = False


class AssignmentDashboardResponse(ORMModel):
    items: list[AssignmentDashboardItem]
