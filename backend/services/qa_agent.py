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
) -> tuple[str, list[dict]]:
    contexts = await rag.search_chunks(db, question=question, course_id=course_id, top_k=top_k)
    system_prompt = "你是课程学习助教，请基于给定资料片段回答问题。要求：用中文，不要输出 JSON。"

    model = get_langchain_chat_model(temperature=0.2)
    if model is not None:
        result = await model.ainvoke(
            [
                ("system", system_prompt),
                ("human", f"问题：{question}\n\n资料片段（contexts）：\n{json.dumps(contexts, ensure_ascii=False)}"),
            ]
        )
        answer = extract_langchain_text(getattr(result, "content", None))
        if answer is not None:
            return answer, contexts

    messages = [
        {"role": "system", "content": "你是课程学习助教，请基于给定资料片段回答问题。"},
        {"role": "user", "content": question},
        {"role": "user", "content": json.dumps({"contexts": contexts}, ensure_ascii=False)},
    ]
    answer = chat_completion(messages)
    if answer is None:
        text = "\n\n".join([c["content"] for c in contexts[:3]])
        answer = f"基于已入库的资料片段：\n{text}\n\n问题：{question}"
    return answer, contexts
