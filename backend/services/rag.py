"""实现检索增强生成流程，包括召回、重排与上下文拼装。"""

import json
import math
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.crud import resource_chunks_crud
from backend.models.course_chapters_mod import CourseChapter
from backend.models.course_resources_mod import CourseResource
from backend.schemas.resource_chunks_sch import ResourceChunkCreate

TEXT_RESOURCE_SUFFIXES = {".txt", ".md"}


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 120) -> list[str]:
    if not text:
        return []
    text = text.strip()
    if not text:
        return []
    if chunk_size <= overlap:
        overlap = 0
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + chunk_size)
        chunks.append(text[start:end])
        if end >= len(text):
            break
        start = end - overlap
    return chunks


def _hash_to_vec(token: str, dim: int) -> list[float]:
    acc = [0.0] * dim
    h = 0
    for ch in token:
        h = (h * 131 + ord(ch)) & 0xFFFFFFFF
    for i in range(dim):
        v = ((h >> (i % 24)) & 0xFF) / 255.0
        acc[i] = v * 2.0 - 1.0
    return acc


def embed_text(text: str, dim: int = 128) -> list[float]:
    tokens = [t for t in text.replace("\n", " ").split(" ") if t]
    if not tokens:
        return [0.0] * dim
    vec = [0.0] * dim
    for token in tokens[:200]:
        tvec = _hash_to_vec(token, dim)
        for i in range(dim):
            vec[i] += tvec[i]
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(x * x for x in b)) or 1.0
    return dot / (na * nb)


def embedding_to_str(vec: list[float]) -> str:
    return json.dumps(vec, ensure_ascii=False)


def embedding_from_str(data: str) -> list[float]:
    try:
        vec = json.loads(data)
        if isinstance(vec, list) and all(isinstance(x, (int, float)) for x in vec):
            return [float(x) for x in vec]
    except Exception:
        return []
    return []


def read_resource_text(resource: CourseResource) -> str:
    content = resource.resource_content or ""
    p = Path(content)
    if p.exists() and p.is_file() and p.suffix.lower() in TEXT_RESOURCE_SUFFIXES:
        return p.read_text(encoding="utf-8", errors="ignore")
    return content


def can_vectorize_resource(resource: CourseResource) -> tuple[bool, str | None]:
    content = (resource.resource_content or "").strip()
    if not content:
        return False, "资源内容为空，无法向量化。"

    p = Path(content)
    if p.exists() and p.is_file():
        if p.suffix.lower() not in TEXT_RESOURCE_SUFFIXES:
            return False, f"当前仅支持 {', '.join(sorted(TEXT_RESOURCE_SUFFIXES))} 文本文件自动向量化。"
        return True, None

    return True, None


async def vectorize_resource(db: AsyncSession, resource_id: int) -> int:
    resource = await db.get(CourseResource, resource_id)
    if resource is None:
        return 0
    text = read_resource_text(resource)
    chunks = chunk_text(text)
    items: list[ResourceChunkCreate] = []
    for idx, chunk in enumerate(chunks):
        vec = embed_text(chunk)
        items.append(
            ResourceChunkCreate(
                resource_id=resource_id,
                chunk_index=idx,
                content=chunk,
                embedding=embedding_to_str(vec),
            )
        )
    await resource_chunks_crud.upsert_chunks(db, resource_id=resource_id, chunks=items)
    return len(items)


async def list_resource_ids_for_course(db: AsyncSession, course_id: int) -> list[int]:
    stmt = (
        select(CourseResource.resource_id)
        .join(CourseChapter, CourseChapter.chapter_id == CourseResource.chapter_id)
        .where(CourseChapter.course_id == course_id)
    )
    result = await db.execute(stmt)
    return [int(x) for x in result.scalars().all()]


async def search_chunks(
    db: AsyncSession,
    question: str,
    course_id: int | None = None,
    top_k: int = 5,
) -> list[dict]:
    qvec = embed_text(question)
    if course_id is None:
        chunks = await resource_chunks_crud.list_chunks(db)
    else:
        resource_ids = await list_resource_ids_for_course(db, course_id)
        chunks = []
        for rid in resource_ids:
            chunks.extend(await resource_chunks_crud.list_chunks(db, resource_id=rid))

    scored = []
    for chunk in chunks:
        vec = embedding_from_str(chunk.embedding)
        score = cosine_similarity(qvec, vec)
        scored.append((score, chunk))
    scored.sort(key=lambda x: x[0], reverse=True)
    out = []
    for score, chunk in scored[:top_k]:
        out.append(
            {
                "resource_id": chunk.resource_id,
                "chunk_id": chunk.chunk_id,
                "content": chunk.content,
                "score": float(score),
            }
        )
    return out
