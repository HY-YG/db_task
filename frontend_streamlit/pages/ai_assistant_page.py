from __future__ import annotations

from typing import Any

import streamlit as st


def render_ai_assistant_page(
    *,
    current_course_id: int | None,
    contexts: list[dict[str, Any]],
    pending_permission_reason: str | None,
) -> str | None:
    st.markdown("<h2 style='margin-bottom: 0;'>统一 AI 助手</h2>", unsafe_allow_html=True)
    st.caption("你的全能学习教练")
    st.write("")

    with st.container(border=True):
        st.markdown(
            f"**当前上下文:** {('已关联课程 #' + str(current_course_id)) if current_course_id else '未选择课程，当前可进行通用聊天'}"
        )
        st.markdown(f"**本轮状态:** {st.session_state.assistant_status_text}")

    if pending_permission_reason:
        st.warning(pending_permission_reason)
        if st.button("同意读取个人学习资料并继续分析", use_container_width=True, type="primary", key="confirm-personal-context"):
            return "__CONFIRM_PERMISSION__"

    for message in st.session_state.assistant_messages:
        role = "assistant" if message.get("role") == "assistant" else "user"
        with st.chat_message(role):
            st.write(message.get("content") or "")
            if role == "assistant" and message.get("extra"):
                extra = message["extra"]
                if extra.get("mode"):
                    st.caption(f"模式：{extra.get('mode')}")

    if contexts:
        with st.expander("查看本轮引用的上下文来源", expanded=False):
            for item in contexts:
                with st.container(border=True):
                    if item.get("memory_kind"):
                        st.markdown(f"**记忆类型**：{item.get('memory_kind')}")
                    if item.get("content"):
                        st.write(item.get("content"))
                    elif item.get("summary_text"):
                        st.write(item.get("summary_text"))
                    if item.get("topics"):
                        st.caption(" / ".join([str(topic) for topic in item.get("topics", [])]))

    return st.chat_input("和 AI 助手聊聊你的课程、作业、笔记或学习计划")
