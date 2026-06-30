"""定义通知消息相关的请求体、响应体与数据校验模型。"""

from datetime import datetime

from pydantic import Field

from backend.schemas.base import ORMModel


class NotificationCreate(ORMModel):
    user_id: int
    notification_content: str
    is_read: bool = False


class NotificationUpdate(ORMModel):
    notification_content: str | None = None
    is_read: bool | None = None


class CourseNotificationPublishRequest(ORMModel):
    sender_user_id: int
    course_id: int
    notification_content: str


class CourseNotificationBatchDeleteRequest(ORMModel):
    sender_user_id: int
    course_id: int
    notification_content: str


class SentCourseNotificationResponse(ORMModel):
    notification_content: str
    sent_at: datetime
    recipient_count: int = Field(..., ge=0)


class NotificationResponse(ORMModel):
    notification_id: int
    user_id: int
    notification_content: str
    sent_at: datetime
    is_read: bool
