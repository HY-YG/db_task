from typing import Any

from backend.services.llm import get_langchain_chat_model


def extract_langchain_text(content: Any) -> str | None:
    if isinstance(content, str) and content.strip():
        return content.strip()
    if isinstance(content, list):
        text_parts = []
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                text_parts.append(part.get("text", ""))
        merged = "".join(text_parts).strip()
        if merged:
            return merged
    return None


def extract_text_from_agent_result(result: dict[str, Any]) -> str | None:
    messages = result.get("messages", [])
    for message in reversed(messages):
        text = extract_langchain_text(getattr(message, "content", None))
        if text is not None:
            return text
    return None


async def invoke_chat_model_text(*, system_prompt: str, user_content: str, temperature: float = 0.2) -> str | None:
    model = get_langchain_chat_model(temperature=temperature)
    if model is None:
        return None
    result = await model.ainvoke(
        [
            ("system", system_prompt),
            ("human", user_content),
        ]
    )
    return extract_langchain_text(getattr(result, "content", None))
