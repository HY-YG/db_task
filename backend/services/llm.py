"""统一管理大模型客户端、模型配置与调用入口。"""

import json
import os
import urllib.request

from langchain_openai import ChatOpenAI


def _get_llm_config() -> dict | None:
    base = os.getenv("LLM_API_BASE")
    key = os.getenv("LLM_API_KEY")
    model = os.getenv("LLM_MODEL")
    if not base or not key or not model:
        return None
    return {"base": base.rstrip("/"), "key": key, "model": model}


def get_langchain_chat_model(temperature: float = 0.2) -> ChatOpenAI | None:
    cfg = _get_llm_config()
    if cfg is None:
        return None
    try:
        return ChatOpenAI(
            model=cfg["model"],
            api_key=cfg["key"],
            base_url=cfg["base"],
            temperature=temperature,
        )
    except Exception:
        return None


def chat_completion(messages: list[dict], temperature: float = 0.2) -> str | None:
    cfg = _get_llm_config()
    if cfg is None:
        return None

    try:
        url = f"{cfg['base']}/v1/chat/completions"
        payload = {"model": cfg["model"], "messages": messages, "temperature": temperature}
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {cfg['key']}"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode("utf-8")
        obj = json.loads(raw)
        return obj["choices"][0]["message"]["content"]
    except Exception:
        return None
