from __future__ import annotations

import streamlit as st

from frontend_streamlit.config import DEFAULT_USER_ID


def init_state() -> None:
    defaults = {
        "current_page": "courses",
        "current_user_id": DEFAULT_USER_ID,
        "selected_course_id": None,
        "assistant_session_id": None,
        "assistant_messages": [],
        "assistant_contexts": [],
        "assistant_status_text": "欢迎使用统一 AI 助手，你可以直接问课程问题，也可以让我帮你做学习分析。",
        "pending_permission_request": False,
        "pending_permission_reason": None,
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
