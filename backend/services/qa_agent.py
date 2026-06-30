"""封装课程问答代理，基于检索上下文生成知识问答结果。"""

import json

from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.langchain_utils import extract_langchain_text
from backend.services import rag
from backend.services.llm import chat_completion, get_langchain_chat_model


async def handle_qa(
    *,
    db: AsyncSession,
    question: str,
    course_id: int | None,
    top_k: int,
    recent_history: list[dict[str, str]] | None = None,
    memory_contexts: list[dict] | None = None,
) -> tuple[str, list[dict]]:
    contexts = await rag.search_chunks(db, question=question, course_id=course_id, top_k=top_k)
    system_prompt = "你是课程学习助教，请基于给定资料片段回答问题。要求：用中文，不要输出 JSON。"
    history_text = "无"
    if recent_history:
        history_text = "\n".join(
            [f"{'用户' if item['role'] == 'user' else '助手'}: {item['content']}" for item in recent_history]
        )
    memory_text = "无"
    if memory_contexts:
        lines = []
        for index, item in enumerate(memory_contexts, start=1):
            lines.append(f"[记忆{index}] 摘要: {item.get('summary_text', '')}")
            topics = item.get("topics", [])
            if topics:
                lines.append(f"主题: {', '.join([str(topic) for topic in topics])}")
            weak_points = item.get("weak_points", [])
            if weak_points:
                lines.append(f"薄弱点: {', '.join([str(point) for point in weak_points])}")
        memory_text = "\n".join(lines)

    model = get_langchain_chat_model(temperature=0.2)
    if model is not None:
        result = await model.ainvoke(
            [
                ("system", system_prompt),
                ("human", f"最近几轮对话：\n{history_text}\n\n相关摘要记忆：\n{memory_text}\n\n问题：{question}\n\n资料片段（contexts）：\n{json.dumps(contexts, ensure_ascii=False)}"),
            ]
        )
        answer = extract_langchain_text(getattr(result, "content", None))
        if answer is not None:
            return answer, contexts

    messages = [
        {"role": "system", "content": "你是课程学习助教，请基于给定资料片段回答问题。"},
        {"role": "user", "content": f"最近几轮对话：\n{history_text}"},
        {"role": "user", "content": f"相关摘要记忆：\n{memory_text}"},
        {"role": "user", "content": question},
        {"role": "user", "content": json.dumps({"contexts": contexts}, ensure_ascii=False)},
    ]
    answer = chat_completion(messages)
    if answer is None:
        text = "\n\n".join([c["content"] for c in contexts[:3]])
        answer = f"基于已入库的资料片段：\n{text}\n\n问题：{question}"
    return answer, contexts
