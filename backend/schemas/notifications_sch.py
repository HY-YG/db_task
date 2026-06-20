from datetime import datetime

from backend.schemas.base import ORMModel


class NotificationCreate(ORMModel):
    user_id: int
    notification_content: str
    is_read: bool = False


class NotificationUpdate(ORMModel):
    notification_content: str | None = None
    is_read: bool | None = None


class NotificationResponse(ORMModel):
    notification_id: int
    user_id: int
    notification_content: str
    sent_at: datetime
    is_read: bool
