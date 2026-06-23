import json
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.crud import ai_memories_crud
from backend.schemas.ai_sch import AiMemoryCreate, AiMemoryResponse
from backend.services.embeddings import embed_text as embed_text_remote
from backend.services.langchain_utils import invoke_chat_model_text


def _parse_summary_json(text: str | None) -> dict[str, Any] | None:
    if text is None:
        return None
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = [line for line in stripped.splitlines() if not line.strip().startswith("```")]
        stripped = "\n".join(lines).strip()
    try:
        data = json.loads(stripped)
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def _format_history(history: list[dict[str, str]]) -> str:
    if not history:
        return "无"
    return "\n".join([f"{'用户' if item['role'] == 'user' else '助手'}: {item['content']}" for item in history])


def _as_str_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _build_memory_embedding_text(
    *,
    summary_text: str,
    topics: list[str],
    weak_points: list[str],
    goals: list[str],
    next_actions: list[str],
) -> str:
    parts = [summary_text]
    if topics:
        parts.append("主题: " + " ".join(topics))
    if weak_points:
        parts.append("薄弱点: " + " ".join(weak_points))
    if goals:
        parts.append("目标: " + " ".join(goals))
    if next_actions:
        parts.append("下一步: " + " ".join(next_actions))
    return "\n".join([part for part in parts if part.strip()])


def _collect_memory_keywords(memory: AiMemoryResponse) -> list[str]:
    meta = memory.memory_meta
    keywords: list[str] = []
    for field in ("topics", "weak_points", "goals", "next_actions"):
        value = meta.get(field, [])
        if isinstance(value, list):
            keywords.extend([str(item).strip() for item in value if str(item).strip()])
    return keywords


def _score_memory(memory: AiMemoryResponse, question: str) -> int:
    score = 0
    normalized_question = question.strip()
    for keyword in _collect_memory_keywords(memory):
        if keyword and keyword in normalized_question:
            score += 3
        elif normalized_question and normalized_question in keyword:
            score += 2
    if memory.summary_text and any(fragment in memory.summary_text for fragment in normalized_question.split()):
        score += 1
    return score


async def summarize_history_to_memory(
    *,
    db: AsyncSession,
    session_id: int,
    user_id: int,
    course_id: int | None,
    history: list[dict[str, str]],
    memory_kind: str = "dialogue_summary",
    coach_stage: str | None = None,
    extra_meta: dict[str, Any] | None = None,
) -> AiMemoryResponse | None:
    if not history:
        return None

    system_prompt = (
        "你是学习助手系统中的记忆摘要器。\n"
        "请根据给定对话，输出一个 JSON 对象，不要输出额外解释，不要使用 Markdown。\n"
        '必须包含字段：summary_text, topics, weak_points, goals, next_actions。\n'
        "其中：\n"
        "- summary_text: 一段中文摘要，概括这段对话最重要的信息。\n"
        "- topics: 主题标签数组。\n"
        "- weak_points: 用户当前暴露出的薄弱点数组，没有则空数组。\n"
        "- goals: 用户当前目标数组，没有则空数组。\n"
        "- next_actions: 建议的下一步动作数组，没有则空数组。\n"
        '最终只输出形如 {"summary_text":"...","topics":["..."],"weak_points":[],"goals":[],"next_actions":[]} 的 JSON。'
    )
    user_content = (
        f"session_id={session_id}\n"
        f"user_id={user_id}\n"
        f"course_id={course_id}\n"
        f"memory_kind={memory_kind}\n"
        f"coach_stage={coach_stage}\n"
        f"最近一段对话：\n{_format_history(history)}"
    )
    raw = await invoke_chat_model_text(system_prompt=system_prompt, user_content=user_content, temperature=0.2)
    parsed = _parse_summary_json(raw)
    if parsed is None:
        return None

    summary_text = str(parsed.get("summary_text", "")).strip()
    if not summary_text:
        return None

    topics = _as_str_list(parsed.get("topics"))
    weak_points = _as_str_list(parsed.get("weak_points"))
    goals = _as_str_list(parsed.get("goals"))
    next_actions = _as_str_list(parsed.get("next_actions"))
    embedding_text = _build_memory_embedding_text(
        summary_text=summary_text,
        topics=topics,
        weak_points=weak_points,
        goals=goals,
        next_actions=next_actions,
    )
    embedding = embed_text_remote(embedding_text)

    memory = await ai_memories_crud.create_memory(
        db,
        AiMemoryCreate(
            session_id=session_id,
            user_id=user_id,
            course_id=course_id,
            memory_kind=memory_kind,
            coach_stage=coach_stage,
            summary_text=summary_text,
            memory_meta={
                "topics": topics,
                "weak_points": weak_points,
                "goals": goals,
                "next_actions": next_actions,
                "source_message_count": len(history),
                **(extra_meta or {}),
            },
        ),
        embedding=embedding,
    )
    return AiMemoryResponse.model_validate(memory)


async def summarize_text_to_memory(
    *,
    db: AsyncSession,
    session_id: int,
    user_id: int,
    course_id: int | None,
    source_text: str,
    memory_kind: str,
    coach_stage: str | None = None,
    extra_meta: dict[str, Any] | None = None,
) -> AiMemoryResponse | None:
    text = source_text.strip()
    if not text:
        return None

    system_prompt = (
        "你是学习助手系统中的记忆整理器。\n"
        "请根据给定内容，输出一个 JSON 对象，不要输出额外解释，不要使用 Markdown。\n"
        '必须包含字段：summary_text, topics, weak_points, goals, next_actions。\n'
        "其中：\n"
        "- summary_text: 一段中文摘要，概括这段内容最重要的信息。\n"
        "- topics: 主题标签数组。\n"
        "- weak_points: 用户当前暴露出的薄弱点数组，没有则空数组。\n"
        "- goals: 用户当前目标数组，没有则空数组。\n"
        "- next_actions: 建议的下一步动作数组，没有则空数组。\n"
        '最终只输出形如 {"summary_text":"...","topics":["..."],"weak_points":[],"goals":[],"next_actions":[]} 的 JSON。'
    )
    user_content = (
        f"session_id={session_id}\n"
        f"user_id={user_id}\n"
        f"course_id={course_id}\n"
        f"memory_kind={memory_kind}\n"
        f"coach_stage={coach_stage}\n"
        f"需要整理的内容：\n{text}"
    )
    raw = await invoke_chat_model_text(system_prompt=system_prompt, user_content=user_content, temperature=0.2)
    parsed = _parse_summary_json(raw)
    if parsed is None:
        return None

    summary_text = str(parsed.get("summary_text", "")).strip()
    if not summary_text:
        return None

    topics = _as_str_list(parsed.get("topics"))
    weak_points = _as_str_list(parsed.get("weak_points"))
    goals = _as_str_list(parsed.get("goals"))
    next_actions = _as_str_list(parsed.get("next_actions"))
    embedding_text = _build_memory_embedding_text(
        summary_text=summary_text,
        topics=topics,
        weak_points=weak_points,
        goals=goals,
        next_actions=next_actions,
    )
    embedding = embed_text_remote(embedding_text)

    memory = await ai_memories_crud.create_memory(
        db,
        AiMemoryCreate(
            session_id=session_id,
            user_id=user_id,
            course_id=course_id,
            memory_kind=memory_kind,
            coach_stage=coach_stage,
            summary_text=summary_text,
            memory_meta={
                "topics": topics,
                "weak_points": weak_points,
                "goals": goals,
                "next_actions": next_actions,
                "source_text_length": len(text),
                **(extra_meta or {}),
            },
        ),
        embedding=embedding,
    )
    return AiMemoryResponse.model_validate(memory)


async def list_relevant_memories(
    *,
    db: AsyncSession,
    user_id: int,
    session_id: int | None = None,
    course_id: int | None = None,
    memory_kind: str | None = None,
    coach_stage: str | None = None,
    topic: str | None = None,
    limit: int = 5,
) -> list[AiMemoryResponse]:
    items = await ai_memories_crud.list_memories(
        db,
        user_id=user_id,
        session_id=session_id,
        course_id=course_id,
        memory_kind=memory_kind,
        coach_stage=coach_stage,
        topic=topic,
        limit=limit,
    )
    return [AiMemoryResponse.model_validate(item) for item in items]


async def get_memory_contexts(
    *,
    db: AsyncSession,
    user_id: int,
    session_id: int | None = None,
    course_id: int | None = None,
    question: str,
    limit: int = 3,
) -> list[dict[str, Any]]:
    query_embedding = embed_text_remote(question)
    if not query_embedding:
        memories = await list_relevant_memories(
            db=db,
            user_id=user_id,
            session_id=session_id,
            course_id=course_id,
            limit=max(limit * 3, 6),
        )
        ranked = sorted(memories, key=lambda item: (_score_memory(item, question), item.created_at), reverse=True)
        selected = ranked[:limit]
        contexts: list[dict[str, Any]] = []
        for item in selected:
            contexts.append(
                {
                    "memory_id": item.memory_id,
                    "memory_kind": item.memory_kind,
                    "coach_stage": item.coach_stage,
                    "summary_text": item.summary_text,
                    "topics": item.memory_meta.get("topics", []),
                    "weak_points": item.memory_meta.get("weak_points", []),
                    "goals": item.memory_meta.get("goals", []),
                    "next_actions": item.memory_meta.get("next_actions", []),
                    "score": float(_score_memory(item, question)),
                    "keyword_score": _score_memory(item, question),
                }
            )
        return contexts

    rows = await ai_memories_crud.search_memories_by_embedding(
        db,
        user_id=user_id,
        query_embedding=query_embedding,
        session_id=session_id,
        course_id=course_id,
        limit=max(limit, 1),
    )
    contexts: list[dict[str, Any]] = []
    for memory, distance in rows:
        similarity = 1.0 - float(distance)
        contexts.append(
            {
                "memory_id": memory.memory_id,
                "memory_kind": memory.memory_kind,
                "coach_stage": memory.coach_stage,
                "summary_text": memory.summary_text,
                "topics": memory.memory_meta.get("topics", []),
                "weak_points": memory.memory_meta.get("weak_points", []),
                "goals": memory.memory_meta.get("goals", []),
                "next_actions": memory.memory_meta.get("next_actions", []),
                "score": float(similarity),
                "keyword_score": int(_score_memory(AiMemoryResponse.model_validate(memory), question)),
            }
        )
    return contexts
