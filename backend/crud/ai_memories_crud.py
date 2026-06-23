from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.ai_memories_mod import AiMemory
from backend.schemas.ai_sch import AiMemoryCreate


async def create_memory(db: AsyncSession, payload: AiMemoryCreate, *, embedding: list[float] | None = None) -> AiMemory:
    memory = AiMemory(**payload.model_dump(exclude_none=True), embedding=embedding)
    db.add(memory)
    await db.commit()
    await db.refresh(memory)
    return memory


async def list_memories(
    db: AsyncSession,
    *,
    user_id: int,
    session_id: int | None = None,
    course_id: int | None = None,
    memory_kind: str | None = None,
    coach_stage: str | None = None,
    topic: str | None = None,
    limit: int = 10,
) -> list[AiMemory]:
    stmt = select(AiMemory).where(AiMemory.user_id == user_id)
    if session_id is not None:
        stmt = stmt.where(AiMemory.session_id == session_id)
    if course_id is not None:
        stmt = stmt.where(AiMemory.course_id == course_id)
    if memory_kind is not None:
        stmt = stmt.where(AiMemory.memory_kind == memory_kind)
    if coach_stage is not None:
        stmt = stmt.where(AiMemory.coach_stage == coach_stage)
    if topic is not None:
        stmt = stmt.where(AiMemory.memory_meta.contains({"topics": [topic]}))
    stmt = stmt.order_by(AiMemory.created_at.desc(), AiMemory.memory_id.desc()).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def search_memories_by_embedding(
    db: AsyncSession,
    *,
    user_id: int,
    query_embedding: list[float],
    session_id: int | None = None,
    course_id: int | None = None,
    limit: int = 5,
) -> list[tuple[AiMemory, float]]:
    distance = AiMemory.embedding.cosine_distance(query_embedding).label("distance")
    stmt = select(AiMemory, distance).where(AiMemory.user_id == user_id, AiMemory.embedding.is_not(None))
    if session_id is not None:
        stmt = stmt.where(AiMemory.session_id == session_id)
    if course_id is not None:
        stmt = stmt.where(AiMemory.course_id == course_id)
    stmt = stmt.order_by(distance.asc(), AiMemory.created_at.desc(), AiMemory.memory_id.desc()).limit(limit)
    result = await db.execute(stmt)
    return [(row[0], float(row[1])) for row in result.all()]
