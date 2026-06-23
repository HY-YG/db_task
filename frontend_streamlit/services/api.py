from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests

from frontend_streamlit.config import DEFAULT_BASE_URL


@dataclass
class ApiResult:
    ok: bool
    data: Any = None
    message: str | None = None


class ApiClient:
    def __init__(self, base_url: str = DEFAULT_BASE_URL) -> None:
        self.base_url = base_url.rstrip("/")

    def get_user(self, user_id: int) -> ApiResult:
        return self._get(f"/api/users/{user_id}")

    def update_user(self, user_id: int, payload: dict[str, Any]) -> ApiResult:
        return self._put(f"/api/users/{user_id}", payload)

    def list_courses(self) -> ApiResult:
        return self._get("/api/courses")

    def list_notes(self, *, user_id: int, course_id: int | None = None) -> ApiResult:
        params: dict[str, Any] = {"user_id": user_id}
        if course_id is not None:
            params["course_id"] = course_id
        return self._get("/api/learning/notes", params=params)

    def create_note(self, payload: dict[str, Any]) -> ApiResult:
        return self._post("/api/learning/notes", payload)

    def list_study_plans(self, *, user_id: int) -> ApiResult:
        return self._get("/api/learning/study-plans", params={"user_id": user_id})

    def create_study_plan(self, payload: dict[str, Any]) -> ApiResult:
        return self._post("/api/learning/study-plans", payload)

    def list_notifications(self, *, user_id: int) -> ApiResult:
        return self._get("/api/learning/notifications", params={"user_id": user_id})

    def list_assignments(self, *, course_id: int | None = None) -> ApiResult:
        params: dict[str, Any] = {}
        if course_id is not None:
            params["course_id"] = course_id
        return self._get("/api/assignments", params=params)

    def create_ai_session(self, *, user_id: int) -> ApiResult:
        return self._post("/api/ai/sessions", {"user_id": user_id, "session_status": "进行中"})

    def assistant_chat(
        self,
        *,
        session_id: int,
        user_id: int,
        message: str,
        course_id: int | None = None,
        confirm_personal_context: bool = False,
    ) -> ApiResult:
        payload: dict[str, Any] = {
            "session_id": session_id,
            "user_id": user_id,
            "message": message,
            "course_id": course_id,
            "top_k": 5,
            "confirm_personal_context": confirm_personal_context,
        }
        return self._post("/api/ai/assistant/chat", payload)

    def _get(self, path: str, params: dict[str, Any] | None = None) -> ApiResult:
        return self._request("GET", path, params=params)

    def _post(self, path: str, payload: dict[str, Any]) -> ApiResult:
        return self._request("POST", path, json=payload)

    def _put(self, path: str, payload: dict[str, Any]) -> ApiResult:
        return self._request("PUT", path, json=payload)

    def _request(self, method: str, path: str, **kwargs: Any) -> ApiResult:
        url = f"{self.base_url}{path}"
        try:
            response = requests.request(method, url, timeout=20, **kwargs)
            response.raise_for_status()
            payload = response.json()
            if isinstance(payload, dict) and "data" in payload:
                return ApiResult(ok=True, data=payload.get("data"), message=payload.get("message"))
            return ApiResult(ok=True, data=payload, message="success")
        except Exception as exc:
            return ApiResult(ok=False, data=None, message=str(exc))

