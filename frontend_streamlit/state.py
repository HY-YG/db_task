"""统一管理 Streamlit 会话状态、登录状态与页面跳转状态。"""

from __future__ import annotations

import streamlit as st


def _default_assistant_status() -> str:
    return "欢迎使用统一 AI 助手，你可以直接问课程问题，也可以让我帮你做学习分析。"


def init_state() -> None:
    # 所有页面共享的状态都在这里集中兜底初始化，避免刷新后出现 KeyError。
    defaults = {
        "current_page": "courses",
        "current_user_id": None,
        "auth_token": None,
        "selected_course_id": None,
        "assistant_session_id": None,
        "assistant_messages": [],
        "assistant_contexts": [],
        "assistant_status_text": _default_assistant_status(),
        "pending_permission_request": False,
        "pending_permission_reason": None,
        "pending_permission_payload": None,
        "assistant_pending_request": None,
        "assistant_permission_policy": "ask",
        "assistant_permission_dialog_action": None,
        "ui_notice": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def apply_query_params() -> None:
    # 彻底弃用基于 URL 的路由刷新机制，改为全内存驱动 SPA
    pass


def set_page(page: str) -> None:
    st.session_state.current_page = page


def reset_assistant_permission_state() -> None:
    st.session_state.pending_permission_request = False
    st.session_state.pending_permission_reason = None
    st.session_state.pending_permission_payload = None
    st.session_state.assistant_permission_dialog_action = None


def reset_user_runtime_state() -> None:
    # 登录用户切换后，需清空与上一个用户绑定的课程、AI 会话和授权临时状态。
    st.session_state.current_page = "courses"
    st.session_state.selected_course_id = None
    st.session_state.assistant_session_id = None
    st.session_state.assistant_messages = []
    st.session_state.assistant_contexts = []
    st.session_state.assistant_status_text = _default_assistant_status()
    reset_assistant_permission_state()


def login_user(user_id: int, token: str) -> None:
    st.session_state.current_user_id = user_id
    st.session_state.auth_token = token
    reset_user_runtime_state()


def logout_user() -> None:
    st.session_state.current_user_id = None
    st.session_state.auth_token = None
    reset_user_runtime_state()
