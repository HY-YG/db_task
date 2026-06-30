"""封装通知消息的数据访问函数，负责常用增删改查与查询组合。"""

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.notifications_mod import Notification
from backend.schemas.notifications_sch import NotificationCreate, NotificationUpdate


async def create_notification(db: AsyncSession, payload: NotificationCreate) -> Notification:
    notification = Notification(**payload.model_dump(exclude_none=True))
    db.add(notification)
    await db.commit()
    await db.refresh(notification)
    return notification


async def create_notifications(db: AsyncSession, payloads: list[NotificationCreate]) -> list[Notification]:
    notifications = [Notification(**payload.model_dump(exclude_none=True)) for payload in payloads]
    db.add_all(notifications)
    await db.commit()
    for notification in notifications:
        await db.refresh(notification)
    return notifications


async def list_notifications(db: AsyncSession, user_id: int | None = None) -> list[Notification]:
    stmt = select(Notification)
    if user_id is not None:
        stmt = stmt.where(Notification.user_id == user_id)
    result = await db.execute(stmt.order_by(Notification.sent_at.desc()))
    return list(result.scalars().all())


async def list_notifications_by_prefix(db: AsyncSession, prefix: str) -> list[Notification]:
    stmt = select(Notification).where(Notification.notification_content.like(f"{prefix}%"))
    result = await db.execute(stmt.order_by(Notification.sent_at.desc(), Notification.notification_id.desc()))
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


async def delete_notifications_by_content(db: AsyncSession, notification_content: str) -> int:
    result = await db.execute(
        delete(Notification).where(Notification.notification_content == notification_content)
    )
    await db.commit()
    return int(result.rowcount or 0)
