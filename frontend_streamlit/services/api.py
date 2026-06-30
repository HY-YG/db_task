"""封装前端访问后端接口的方法、缓存包装与缓存清理逻辑。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests
import streamlit as st
from requests.adapters import HTTPAdapter
from streamlit.runtime.uploaded_file_manager import UploadedFile

from frontend_streamlit.config import DEFAULT_BASE_URL


@dataclass
class ApiResult:
    ok: bool
    data: Any = None
    message: str | None = None


def to_cached_result(result: ApiResult) -> dict[str, Any]:
    return {
        "ok": result.ok,
        "data": result.data,
        "message": result.message,
    }


def restore_api_result(payload: dict[str, Any] | None) -> ApiResult:
    if not isinstance(payload, dict):
        return ApiResult(ok=False, data=None, message="缓存结果无效")
    return ApiResult(
        ok=bool(payload.get("ok")),
        data=payload.get("data"),
        message=payload.get("message"),
    )


class ApiClient:
    def __init__(self, base_url: str = DEFAULT_BASE_URL, session: requests.Session | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.session = session or build_http_session()

    def get_user(self, user_id: int) -> ApiResult:
        return self._get(f"/api/user/detail/{user_id}")

    def login(self, payload: dict[str, Any]) -> ApiResult:
        return self._post("/api/auth/login", payload)

    def register(self, payload: dict[str, Any]) -> ApiResult:
        return self._post("/api/auth/register", payload)

    def logout(self) -> ApiResult:
        return self._post("/api/auth/logout", {})

    def get_current_user(self) -> ApiResult:
        return self._get("/api/auth/me")

    def change_password(self, payload: dict[str, Any]) -> ApiResult:
        return self._put("/api/auth/password", payload)

    def update_user(self, user_id: int, payload: dict[str, Any]) -> ApiResult:
        return self._put(f"/api/user/update/{user_id}", payload)

    def list_users(self) -> ApiResult:
        return self._get("/api/user/list")

    def list_roles(self) -> ApiResult:
        return self._get("/api/role/list")

    def list_courses(self) -> ApiResult:
        return self._get("/api/course/list")

    def get_course_overview(self, user_id: int) -> ApiResult:
        return self._get(f"/api/course/overview/{user_id}")

    def get_course_detail_bundle(self, *, course_id: int, user_id: int) -> ApiResult:
        return self._get(f"/api/course/detail-bundle/{course_id}", params={"user_id": user_id})

    def get_course_management_bundle(self, *, user_id: int | None = None) -> ApiResult:
        params: dict[str, Any] = {}
        if user_id is not None:
            params["user_id"] = user_id
        return self._get("/api/course/management-bundle", params=params)

    def create_course(self, payload: dict[str, Any]) -> ApiResult:
        return self._post("/api/course/add", payload)

    def update_course(self, course_id: int, payload: dict[str, Any]) -> ApiResult:
        return self._put(f"/api/course/update/{course_id}", payload)

    def list_chapters(self, *, course_id: int | None = None) -> ApiResult:
        params: dict[str, Any] = {}
        if course_id is not None:
            params["course_id"] = course_id
        return self._get("/api/course/chapter/list", params=params)

    def create_chapter(self, payload: dict[str, Any]) -> ApiResult:
        return self._post("/api/course/chapter/add", payload)

    def update_chapter(self, chapter_id: int, payload: dict[str, Any]) -> ApiResult:
        return self._put(f"/api/course/chapter/update/{chapter_id}", payload)

    def list_resources(self, *, chapter_id: int | None = None) -> ApiResult:
        params: dict[str, Any] = {}
        if chapter_id is not None:
            params["chapter_id"] = chapter_id
        return self._get("/api/course/resource/list", params=params)

    def create_resource(self, payload: dict[str, Any]) -> ApiResult:
        return self._post("/api/course/resource/add", payload)

    def update_resource(self, resource_id: int, payload: dict[str, Any]) -> ApiResult:
        return self._put(f"/api/course/resource/update/{resource_id}", payload)

    def upload_resource(
        self,
        *,
        chapter_id: int,
        uploaded_file: UploadedFile,
        resource_title: str | None = None,
        version_description: str | None = None,
    ) -> ApiResult:
        files = {
            "file": (
                uploaded_file.name,
                uploaded_file.getvalue(),
                uploaded_file.type or "application/octet-stream",
            )
        }
        data = {
            "chapter_id": str(chapter_id),
            "resource_title": resource_title or uploaded_file.name,
            "version_description": version_description or "",
        }
        return self._request("POST", "/api/ai/upload", data=data, files=files)

    def list_enrollments(self, *, user_id: int | None = None, course_id: int | None = None) -> ApiResult:
        params: dict[str, Any] = {}
        if user_id is not None:
            params["user_id"] = user_id
        if course_id is not None:
            params["course_id"] = course_id
        return self._get("/api/course/enrollment/list", params=params)

    def create_enrollment(self, payload: dict[str, Any]) -> ApiResult:
        return self._post("/api/course/enrollment/add", payload)

    def list_teaching_relations(self, *, user_id: int | None = None) -> ApiResult:
        params: dict[str, Any] = {}
        if user_id is not None:
            params["user_id"] = user_id
        return self._get("/api/course/teaching/list", params=params)

    def create_teaching_relation(self, payload: dict[str, Any]) -> ApiResult:
        return self._post("/api/course/teaching/add", payload)

    def list_progress(
        self,
        *,
        user_id: int | None = None,
        course_id: int | None = None,
        progress_type: str | None = None,
    ) -> ApiResult:
        params: dict[str, Any] = {}
        if user_id is not None:
            params["user_id"] = user_id
        if course_id is not None:
            params["course_id"] = course_id
        if progress_type is not None:
            params["progress_type"] = progress_type
        return self._get("/api/learning/progress/list", params=params)

    def upsert_progress(self, payload: dict[str, Any]) -> ApiResult:
        return self._post("/api/learning/progress/upsert", payload)

    def list_notes(self, *, user_id: int, course_id: int | None = None) -> ApiResult:
        params: dict[str, Any] = {"user_id": user_id}
        if course_id is not None:
            params["course_id"] = course_id
        return self._get("/api/learning/note/list", params=params)

    def create_note(self, payload: dict[str, Any]) -> ApiResult:
        return self._post("/api/learning/note/add", payload)

    def list_study_plans(self, *, user_id: int) -> ApiResult:
        return self._get("/api/learning/plan/list", params={"user_id": user_id})

    def create_study_plan(self, payload: dict[str, Any]) -> ApiResult:
        return self._post("/api/learning/plan/add", payload)

    def list_notifications(self, *, user_id: int) -> ApiResult:
        return self._get("/api/learning/notification/list", params={"user_id": user_id})

    def update_notification(self, notification_id: int, payload: dict[str, Any]) -> ApiResult:
        return self._put(f"/api/learning/notification/update/{notification_id}", payload)

    def delete_notification(self, notification_id: int) -> ApiResult:
        return self._request("DELETE", f"/api/learning/notification/delete/{notification_id}")

    def publish_course_notification(self, payload: dict[str, Any]) -> ApiResult:
        return self._post("/api/learning/notification/publish-course", payload)

    def list_sent_course_notifications(self, *, sender_user_id: int, course_id: int) -> ApiResult:
        return self._get(
            "/api/learning/notification/sent-course",
            params={"sender_user_id": sender_user_id, "course_id": course_id},
        )

    def delete_course_notification_batch(self, payload: dict[str, Any]) -> ApiResult:
        return self._post("/api/learning/notification/delete-course-batch", payload)

    def list_assignments(self, *, course_id: int | None = None) -> ApiResult:
        params: dict[str, Any] = {}
        if course_id is not None:
            params["course_id"] = course_id
        return self._get("/api/assignment/list", params=params)

    def create_assignment(self, payload: dict[str, Any]) -> ApiResult:
        return self._post("/api/assignment/add", payload)

    def update_assignment(self, assignment_id: int, payload: dict[str, Any]) -> ApiResult:
        return self._put(f"/api/assignment/update/{assignment_id}", payload)

    def delete_assignment(self, assignment_id: int) -> ApiResult:
        return self._request("DELETE", f"/api/assignment/delete/{assignment_id}")

    def get_assignment_dashboard(self, *, user_id: int, course_id: int | None = None) -> ApiResult:
        params: dict[str, Any] = {}
        if course_id is not None:
            params["course_id"] = course_id
        return self._get(f"/api/assignment/dashboard/{user_id}", params=params)

    def list_assignment_submissions(self, *, assignment_id: int, user_id: int | None = None) -> ApiResult:
        params: dict[str, Any] = {}
        if user_id is not None:
            params["user_id"] = user_id
        return self._get(f"/api/assignment/submission/list/{assignment_id}", params=params)

    def create_assignment_submission(self, assignment_id: int, payload: dict[str, Any]) -> ApiResult:
        return self._post(f"/api/assignment/submission/add/{assignment_id}", payload)

    def update_assignment_submission(self, submission_id: int, payload: dict[str, Any]) -> ApiResult:
        return self._put(f"/api/assignment/submission/update/{submission_id}", payload)

    def create_ai_session(self, *, user_id: int) -> ApiResult:
        return self._post("/api/ai/session/add", {"user_id": user_id, "session_status": "进行中"})

    def list_ai_sessions(self, *, user_id: int) -> ApiResult:
        return self._get("/api/ai/session/list", params={"user_id": user_id})

    def list_ai_messages(self, *, session_id: int) -> ApiResult:
        return self._get("/api/ai/message/list", params={"session_id": session_id})

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
        return self._request("POST", "/api/ai/assistant/chat", json=payload, timeout=60)

    def _get(self, path: str, params: dict[str, Any] | None = None) -> ApiResult:
        return self._request("GET", path, params=params)

    def _post(self, path: str, payload: dict[str, Any]) -> ApiResult:
        return self._request("POST", path, json=payload)

    def _put(self, path: str, payload: dict[str, Any]) -> ApiResult:
        return self._request("PUT", path, json=payload)

    def _request(self, method: str, path: str, **kwargs: Any) -> ApiResult:
        url = f"{self.base_url}{path}"
        headers = dict(kwargs.pop("headers", {}))
        # 底层统一托管 timeout，避免上层传参时与默认值重复导致 requests 报错。
        timeout = kwargs.pop("timeout", 15)
        token = st.session_state.get("auth_token")
        if token:
            headers.setdefault("Authorization", f"Bearer {token}")
        if headers:
            kwargs["headers"] = headers
        try:
            response = self.session.request(method, url, timeout=timeout, **kwargs)
            response.raise_for_status()
            payload = response.json()
            if isinstance(payload, dict) and "data" in payload:
                return ApiResult(ok=True, data=payload.get("data"), message=payload.get("message"))
            return ApiResult(ok=True, data=payload, message="success")
        except requests.HTTPError as exc:
            error_message = str(exc)
            response = exc.response
            if response is not None:
                try:
                    error_payload = response.json()
                except ValueError:
                    error_payload = None
                if isinstance(error_payload, dict):
                    # 后端 detail 可能是字符串也可能是校验错误列表，这里统一压平成可展示文本。
                    detail = error_payload.get("detail") or error_payload.get("message")
                    if isinstance(detail, list):
                        detail = "; ".join(str(item) for item in detail)
                    if detail:
                        error_message = str(detail)
                elif response.text:
                    error_message = response.text
            return ApiResult(ok=False, data=None, message=error_message)
        except Exception as exc:
            return ApiResult(ok=False, data=None, message=str(exc))


@st.cache_resource(show_spinner=False)
def build_http_session() -> requests.Session:
    session = requests.Session()
    # 复用连接池可以显著减少 Streamlit 多次刷新带来的重复建连开销。
    adapter = HTTPAdapter(pool_connections=20, pool_maxsize=20, max_retries=0)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


@st.cache_resource(show_spinner=False)
def get_api_client(base_url: str = DEFAULT_BASE_URL) -> ApiClient:
    return ApiClient(base_url=base_url, session=build_http_session())


@st.cache_data(ttl=300, show_spinner=False)
def cached_get_user(user_id: int) -> dict[str, Any]:
    return to_cached_result(get_api_client().get_user(user_id))


@st.cache_data(ttl=300, show_spinner=False)
def cached_list_users() -> dict[str, Any]:
    return to_cached_result(get_api_client().list_users())


@st.cache_data(ttl=300, show_spinner=False)
def cached_list_roles() -> dict[str, Any]:
    return to_cached_result(get_api_client().list_roles())


@st.cache_data(ttl=300, show_spinner=False)
def cached_list_courses() -> dict[str, Any]:
    return to_cached_result(get_api_client().list_courses())


@st.cache_data(ttl=300, show_spinner=False)
def cached_get_course_overview(user_id: int) -> dict[str, Any]:
    return to_cached_result(get_api_client().get_course_overview(user_id))


@st.cache_data(ttl=300, show_spinner=False)
def cached_get_course_detail_bundle(course_id: int, user_id: int) -> dict[str, Any]:
    return to_cached_result(get_api_client().get_course_detail_bundle(course_id=course_id, user_id=user_id))


@st.cache_data(ttl=300, show_spinner=False)
def cached_get_course_management_bundle(user_id: int | None = None) -> dict[str, Any]:
    return to_cached_result(get_api_client().get_course_management_bundle(user_id=user_id))


@st.cache_data(ttl=300, show_spinner=False)
def cached_list_chapters(course_id: int | None = None) -> dict[str, Any]:
    return to_cached_result(get_api_client().list_chapters(course_id=course_id))


@st.cache_data(ttl=300, show_spinner=False)
def cached_list_resources(chapter_id: int | None = None) -> dict[str, Any]:
    return to_cached_result(get_api_client().list_resources(chapter_id=chapter_id))


@st.cache_data(ttl=300, show_spinner=False)
def cached_list_enrollments(user_id: int | None = None, course_id: int | None = None) -> dict[str, Any]:
    return to_cached_result(get_api_client().list_enrollments(user_id=user_id, course_id=course_id))


@st.cache_data(ttl=300, show_spinner=False)
def cached_list_teaching_relations(user_id: int | None = None) -> dict[str, Any]:
    return to_cached_result(get_api_client().list_teaching_relations(user_id=user_id))


@st.cache_data(ttl=300, show_spinner=False)
def cached_list_progress(
    user_id: int | None = None,
    course_id: int | None = None,
    progress_type: str | None = None,
) -> dict[str, Any]:
    return to_cached_result(
        get_api_client().list_progress(user_id=user_id, course_id=course_id, progress_type=progress_type)
    )


@st.cache_data(ttl=300, show_spinner=False)
def cached_list_notes(user_id: int, course_id: int | None = None) -> dict[str, Any]:
    return to_cached_result(get_api_client().list_notes(user_id=user_id, course_id=course_id))


@st.cache_data(ttl=300, show_spinner=False)
def cached_list_study_plans(user_id: int) -> dict[str, Any]:
    return to_cached_result(get_api_client().list_study_plans(user_id=user_id))


@st.cache_data(ttl=300, show_spinner=False)
def cached_list_notifications(user_id: int) -> dict[str, Any]:
    return to_cached_result(get_api_client().list_notifications(user_id=user_id))


@st.cache_data(ttl=300, show_spinner=False)
def cached_list_assignments(course_id: int | None = None) -> dict[str, Any]:
    return to_cached_result(get_api_client().list_assignments(course_id=course_id))


@st.cache_data(ttl=300, show_spinner=False)
def cached_get_assignment_dashboard(user_id: int, course_id: int | None = None) -> dict[str, Any]:
    return to_cached_result(get_api_client().get_assignment_dashboard(user_id=user_id, course_id=course_id))


def clear_user_cache() -> None:
    cached_get_user.clear()
    cached_list_users.clear()
    cached_list_roles.clear()


def clear_course_cache() -> None:
    # 课程域缓存彼此高度关联，课程、进度、作业任一变更后统一失效更安全。
    cached_get_course_overview.clear()
    cached_get_course_detail_bundle.clear()
    cached_get_course_management_bundle.clear()
    cached_list_courses.clear()
    cached_list_chapters.clear()
    cached_list_resources.clear()
    cached_list_enrollments.clear()
    cached_list_teaching_relations.clear()
    cached_list_progress.clear()
    cached_list_assignments.clear()
    cached_get_assignment_dashboard.clear()


def clear_learning_cache() -> None:
    cached_list_notes.clear()
    cached_list_study_plans.clear()
    cached_list_notifications.clear()
