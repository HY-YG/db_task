"""封装统一的接口成功响应结构。"""

from pydantic import BaseModel


def _serialize(data):
    if data is None:
        return None
    if isinstance(data, BaseModel):
        return data.model_dump()
    if isinstance(data, list):
        return [_serialize(item) for item in data]
    return data


def success_response(data=None, message: str = "success", code: int = 200) -> dict:
    return {"code": code, "message": message, "data": _serialize(data)}
