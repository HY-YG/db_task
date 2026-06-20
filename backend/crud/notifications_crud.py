from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.notifications_mod import Notification
from backend.schemas.notifications_sch import NotificationCreate, NotificationUpdate


async def create_notification(db: AsyncSession, payload: NotificationCreate) -> Notification:
    notification = Notification(**payload.model_dump(exclude_none=True))
    db.add(notification)
    await db.commit()
    await db.refresh(notification)
    return notification


async def list_notifications(db: AsyncSession, user_id: int | None = None) -> list[Notification]:
    stmt = select(Notification)
    if user_id is not None:
        stmt = stmt.where(Notification.user_id == user_id)
    result = await db.execute(stmt.order_by(Notification.sent_at.desc()))
    return list(result.scalars().all())


async def get_notification(db: AsyncSession, notification_id: int) -> Notification | None:
    return await db.get(Notification, notification_id)


async def update_notification(db: AsyncSession, notification: Notification, payload: NotificationUpdate) -> Notification:
    for field, value in payload.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(notification, field, value)
    await db.commit()
    await db.refresh(notification)
    return notification


async def delete_notification(db: AsyncSession, notification: Notification) -> None:
    await db.delete(notification)
    await db.commit()
