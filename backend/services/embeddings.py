"""封装向量嵌入模型加载与文本向量化能力。"""

import json
import os
import urllib.request


def _get_embedding_config() -> dict | None:
    base = os.getenv("SILICONFLOW_BASE_URL")
    key = os.getenv("SILICONFLOW_API_KEY")
    model = os.getenv("SILICONFLOW_EMBEDDING_MODEL") or "BAAI/bge-m3"
    if not base or not key:
        return None
    return {"base": base.rstrip("/"), "key": key, "model": model}


def get_embedding_dimension(default: int = 1024) -> int:
    raw = os.getenv("SILICONFLOW_EMBEDDING_DIM")
    if raw:
        try:
            value = int(raw)
            if value > 0:
                return value
        except Exception:
            pass
    return default


def _openai_url(base: str, path: str) -> str:
    normalized_path = path.lstrip("/")
    if base.endswith("/v1"):
        return f"{base}/{normalized_path}"
    return f"{base}/v1/{normalized_path}"


def embed_texts(texts: list[str]) -> list[list[float]] | None:
    cfg = _get_embedding_config()
    if cfg is None:
        return None

    cleaned = [str(text or "") for text in texts]
    if not cleaned:
        return []

    try:
        url = _openai_url(cfg["base"], "/embeddings")
        payload = {"model": cfg["model"], "input": cleaned}
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
        items = obj.get("data", [])
        if not isinstance(items, list):
            return None
        vectors: list[list[float]] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            embedding = item.get("embedding")
            if isinstance(embedding, list) and all(isinstance(x, (int, float)) for x in embedding):
                vectors.append([float(x) for x in embedding])
        return vectors if vectors else None
    except Exception:
        return None


def embed_text(text: str) -> list[float] | None:
    vectors = embed_texts([text])
    if not vectors:
        return None
    return vectors[0]
