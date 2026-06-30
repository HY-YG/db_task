"""封装课程笔记的数据访问函数，负责常用增删改查与查询组合。"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.notes_mod import Note
from backend.schemas.notes_sch import NoteCreate, NoteUpdate


async def create_note(db: AsyncSession, payload: NoteCreate) -> Note:
    note = Note(**payload.model_dump(exclude_none=True))
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return note


async def list_notes(db: AsyncSession, user_id: int | None = None, course_id: int | None = None) -> list[Note]:
    stmt = select(Note)
    if user_id is not None:
        stmt = stmt.where(Note.user_id == user_id)
    if course_id is not None:
        stmt = stmt.where(Note.course_id == course_id)
    result = await db.execute(stmt.order_by(Note.recorded_at.desc()))
    return list(result.scalars().all())


async def list_recent_notes(
    db: AsyncSession,
    *,
    user_id: int,
    course_id: int,
    limit: int = 5,
) -> list[Note]:
    stmt = (
        select(Note)
        .where(Note.user_id == user_id, Note.course_id == course_id)
        .order_by(Note.recorded_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_note(db: AsyncSession, note_id: int) -> Note | None:
    return await db.get(Note, note_id)


async def update_note(db: AsyncSession, note: Note, payload: NoteUpdate) -> Note:
    for field, value in payload.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(note, field, value)
    await db.commit()
    await db.refresh(note)
    return note


async def delete_note(db: AsyncSession, note: Note) -> None:
    await db.delete(note)
    await db.commit()
