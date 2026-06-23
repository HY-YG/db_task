from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.ai_messages_mod import AiMessage
from backend.models.ai_sessions_mod import AiSession
from backend.schemas.ai_sch import AiMessageCreate, AiSessionCreate, AiSessionUpdate


async def create_session(db: AsyncSession, payload: AiSessionCreate) -> AiSession:
    session = AiSession(**payload.model_dump(exclude_none=True))
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def list_sessions(db: AsyncSession, user_id: int | None = None) -> list[AiSession]:
    stmt = select(AiSession)
    if user_id is not None:
        stmt = stmt.where(AiSession.user_id == user_id)
    result = await db.execute(stmt.order_by(AiSession.session_id))
    return list(result.scalars().all())


async def get_session(db: AsyncSession, session_id: int) -> AiSession | None:
    return await db.get(AiSession, session_id)


async def update_session(db: AsyncSession, session: AiSession, payload: AiSessionUpdate) -> AiSession:
    for field, value in payload.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(session, field, value)
    await db.commit()
    await db.refresh(session)
    return session


async def create_message(db: AsyncSession, payload: AiMessageCreate) -> AiMessage:
    message = AiMessage(**payload.model_dump(exclude_none=True))
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message


async def list_messages(db: AsyncSession, session_id: int | None = None) -> list[AiMessage]:
    stmt = select(AiMessage)
    if session_id is not None:
        stmt = stmt.where(AiMessage.session_id == session_id)
    result = await db.execute(stmt.order_by(AiMessage.sent_at))
    return list(result.scalars().all())


async def has_ai_message_json(
    db: AsyncSession,
    *,
    session_id: int,
    message_type: str,
    stage: str | None = None,
) -> bool:
    payload = {"type": message_type}
    if stage is not None:
        payload["stage"] = stage

    stmt = (
        select(AiMessage.message_id)
        .where(AiMessage.session_id == session_id, AiMessage.sender == "ai")
        .where(AiMessage.message_content.contains(payload)) #@>方法
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none() is not None


async def get_latest_ai_message_json(
    db: AsyncSession,
    *,
    session_id: int,
    message_type: str,
    stage: str | None = None,
) -> AiMessage | None:
    payload = {"type": message_type}
    if stage is not None:
        payload["stage"] = stage

    stmt = (
        select(AiMessage)
        .where(AiMessage.session_id == session_id, AiMessage.sender == "ai")
        .where(AiMessage.message_content.contains(payload))
        .order_by(AiMessage.sent_at.desc(), AiMessage.message_id.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()
