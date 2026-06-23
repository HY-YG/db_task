from __future__ import annotations

from typing import Any

import streamlit as st

# 必须在最前面
st.set_page_config(page_title="智学空间", page_icon="🎓", layout="wide")

from frontend_streamlit.components.layout import inject_global_styles, render_side_navigation, render_topbar
from frontend_streamlit.pages.ai_assistant_page import render_ai_assistant_page
from frontend_streamlit.pages.assignments_page import render_assignments_page
from frontend_streamlit.pages.courses_page import render_courses_page
from frontend_streamlit.pages.inbox_page import render_inbox_page
from frontend_streamlit.pages.notes_plans_page import render_notes_plans_page
from frontend_streamlit.services.api import ApiClient
from frontend_streamlit.state import apply_query_params, init_state, reset_assistant_permission_state

api = ApiClient()
init_state()
apply_query_params()
inject_global_styles()


@st.cache_data(ttl=60)
def load_user(user_id: int) -> dict[str, Any]:
    result = api.get_user(user_id)
    if result.ok and isinstance(result.data, dict):
        return result.data
    return {"user_id": user_id, "name": "Teacher Zhang", "gender": "未设置", "age": 0}


def ensure_assistant_session() -> int | None:
    if st.session_state.assistant_session_id is not None:
        return st.session_state.assistant_session_id
    result = api.create_ai_session(user_id=st.session_state.current_user_id)
    if result.ok and isinstance(result.data, dict):
        st.session_state.assistant_session_id = result.data.get("session_id")
        return st.session_state.assistant_session_id
    return None


def build_status_text(payload: dict[str, Any]) -> str:
    mode = payload.get("mode")
    coach_stage = payload.get("coach_stage")
    if mode == "permission_request":
        return "本轮分析需要你的个人学习资料授权。"
    if mode == "coach_started":
        return f"学习教练已启动，当前阶段：{coach_stage or 'coach_diagnose'}。"
    if mode == "personal_analysis":
        return "已进入个性化学习分析模式。"
    if mode == "qa":
        return "本轮回答结合了课程资料上下文。"
    return "当前处于统一 AI 助手对话模式。"


def send_assistant_message(message: str, *, confirm_personal_context: bool = False) -> None:
    session_id = ensure_assistant_session()
    if session_id is None:
        st.error("AI 会话创建失败，请先确认后端服务已启动。")
        return

    if not confirm_personal_context:
        st.session_state.assistant_messages.append({"role": "user", "content": message})

    result = api.assistant_chat(
        session_id=session_id,
        user_id=st.session_state.current_user_id,
        message=message,
        course_id=st.session_state.selected_course_id,
        confirm_personal_context=confirm_personal_context,
    )
    if not result.ok or not isinstance(result.data, dict):
        st.session_state.assistant_messages.append({"role": "assistant", "content": f"请求失败：{result.message or '未知错误'}"})
        return

    payload = result.data
    st.session_state.assistant_status_text = build_status_text(payload)
    st.session_state.assistant_contexts = payload.get("contexts", []) if isinstance(payload.get("contexts"), list) else []
    st.session_state.assistant_messages.append(
        {
            "role": "assistant",
            "content": payload.get("answer") or "助手暂时没有返回内容。",
            "extra": {"mode": payload.get("mode"), "coach_stage": payload.get("coach_stage")},
        }
    )
    if payload.get("permission_required"):
        st.session_state.pending_permission_request = True
        st.session_state.pending_permission_reason = payload.get("permission_reason")
    else:
        reset_assistant_permission_state()


user_info = load_user(st.session_state.current_user_id)

render_topbar(user_info)

st.write("")
st.write("")

left_col, right_col = st.columns([1.5, 6], gap="large")

with left_col:
    render_side_navigation(user_info)

with right_col:
    page = st.session_state.current_page

    if page == "courses":
        courses_res = api.list_courses()
        courses = courses_res.data if courses_res.ok and isinstance(courses_res.data, list) else []
        render_courses_page(courses)

    elif page == "inbox":
        notifs_res = api.list_notifications(user_id=st.session_state.current_user_id)
        notifications = notifs_res.data if notifs_res.ok and isinstance(notifs_res.data, list) else []
        render_inbox_page(notifications)

    elif page == "notes_plans":
        notes_res = api.list_notes(
            user_id=st.session_state.current_user_id, course_id=st.session_state.selected_course_id
        )
        plans_res = api.list_study_plans(user_id=st.session_state.current_user_id)
        notes = notes_res.data if notes_res.ok and isinstance(notes_res.data, list) else []
        plans = plans_res.data if plans_res.ok and isinstance(plans_res.data, list) else []

        payload = render_notes_plans_page(
            notes=notes,
            plans=plans,
            selected_course_id=st.session_state.selected_course_id,
        )
        if payload:
            if payload["type"] == "note":
                res = api.create_note(
                    {
                        "user_id": st.session_state.current_user_id,
                        "course_id": payload["course_id"],
                        "content": payload["content"],
                    }
                )
                if res.ok:
                    st.success("笔记已保存")
                    st.rerun()
            elif payload["type"] == "plan":
                res = api.create_study_plan(
                    {
                        "user_id": st.session_state.current_user_id,
                        "plan_content": payload["plan_content"],
                        "plan_status": payload["plan_status"],
                    }
                )
                if res.ok:
                    st.success("学习计划已保存")
                    st.rerun()

    elif page == "assignments":
        assigns_res = api.list_assignments(course_id=st.session_state.selected_course_id)
        assignments = assigns_res.data if assigns_res.ok and isinstance(assigns_res.data, list) else []
        render_assignments_page(assignments)

    elif page == "ai_assistant":
        message = render_ai_assistant_page(
            current_course_id=st.session_state.selected_course_id,
            contexts=st.session_state.assistant_contexts,
            pending_permission_reason=st.session_state.pending_permission_reason,
        )
        if message == "__CONFIRM_PERMISSION__":
            send_assistant_message("同意", confirm_personal_context=True)
            st.rerun()
        elif isinstance(message, str) and message.strip():
            send_assistant_message(message.strip())
            st.rerun()
