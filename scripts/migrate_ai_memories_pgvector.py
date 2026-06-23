import asyncio
import sys
from pathlib import Path

from sqlalchemy import text

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import backend.models
from backend.config.db_config import Base, engine
from backend.services.embeddings import embed_text, embed_texts, get_embedding_dimension


def _build_embedding_text(summary_text: str, meta: dict) -> str:
    topics = meta.get("topics", [])
    weak_points = meta.get("weak_points", [])
    goals = meta.get("goals", [])
    next_actions = meta.get("next_actions", [])

    def _as_list(value: object) -> list[str]:
        if not isinstance(value, list):
            return []
        return [str(item).strip() for item in value if str(item).strip()]

    parts = [summary_text.strip()]
    topics = _as_list(topics)
    weak_points = _as_list(weak_points)
    goals = _as_list(goals)
    next_actions = _as_list(next_actions)
    if topics:
        parts.append("主题: " + " ".join(topics))
    if weak_points:
        parts.append("薄弱点: " + " ".join(weak_points))
    if goals:
        parts.append("目标: " + " ".join(goals))
    if next_actions:
        parts.append("下一步: " + " ".join(next_actions))
    return "\n".join([part for part in parts if part.strip()])


def _vector_literal(vec: list[float]) -> str:
    return "[" + ",".join([str(float(x)) for x in vec]) + "]"


def _detect_embedding_dimension() -> int:
    detected = embed_text("dimension probe")
    if detected:
        return len(detected)
    return get_embedding_dimension()


async def main() -> None:
    embedding_dim = _detect_embedding_dimension()
    async with engine.begin() as conn:
        await conn.execute(text("create extension if not exists vector"))
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text(f"alter table ai_memories add column if not exists embedding vector({embedding_dim})"))
        await conn.execute(
            text(
                f"alter table ai_memories alter column embedding type vector({embedding_dim}) "
                f"using case when embedding is null then null else embedding::vector({embedding_dim}) end"
            )
        )

        result = await conn.execute(
            text("select memory_id, summary_text, memory_meta from ai_memories where embedding is null order by memory_id")
        )
        rows = list(result.all())

    batch_size = 32
    for offset in range(0, len(rows), batch_size):
        batch = rows[offset : offset + batch_size]
        texts = []
        ids = []
        for memory_id, summary_text, memory_meta in batch:
            ids.append(int(memory_id))
            meta = memory_meta if isinstance(memory_meta, dict) else {}
            texts.append(_build_embedding_text(str(summary_text or ""), meta))

        vectors = embed_texts(texts) or []
        if len(vectors) != len(ids):
            continue

        async with engine.begin() as conn:
            for memory_id, vec in zip(ids, vectors, strict=False):
                await conn.execute(
                    text(
                        f"update ai_memories set embedding = (:embedding)::vector({embedding_dim}) "
                        f"where memory_id = :memory_id"
                    ),
                    {"embedding": _vector_literal(vec), "memory_id": memory_id},
                )
                print(f"OK: ai_memories.embedding backfilled memory_id={memory_id}")

    async with engine.begin() as conn:
        await conn.execute(
            text(
                "create index if not exists idx_ai_memories_embedding_ivfflat "
                "on ai_memories using ivfflat (embedding vector_cosine_ops) with (lists = 100)"
            )
        )
        await conn.execute(text("analyze ai_memories"))
        print(f"OK: index + analyze (dim={embedding_dim})")


if __name__ == "__main__":
    asyncio.run(main())
