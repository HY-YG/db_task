"""渲染 AI 助手页面，组织消息列表、上下文展示与授权交互。"""

from __future__ import annotations

from typing import Any

import streamlit as st


@st.dialog("个人学习资料访问授权", width="large")
def render_personal_context_permission_dialog(reason: str | None) -> None:
    st.markdown("AI 需要读取你的个人学习资料后，才能继续这次个性化分析。")
    st.caption(reason or "将访问你的笔记、学习计划和作业完成情况，仅用于本轮分析。")
    st.info("你可以仅授权本次、拒绝本次，或保存为“始终允许并不再提示”。")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("同意本次", type="primary", use_container_width=True, key="assistant-permission-allow-once"):
            st.session_state.assistant_permission_dialog_action = "allow_once"
            st.rerun()
    with col2:
        if st.button("拒绝", use_container_width=True, key="assistant-permission-deny"):
            st.session_state.assistant_permission_dialog_action = "deny"
            st.rerun()
    with col3:
        if st.button("始终允许并不再提示", use_container_width=True, key="assistant-permission-allow-always"):
            st.session_state.assistant_permission_dialog_action = "always_allow"
            st.rerun()


def render_ai_assistant_page(
    *,
    current_course_id: int | None,
    contexts: list[dict[str, Any]],
    pending_permission_reason: str | None,
    permission_policy: str,
) -> str | None:
    st.markdown("<h2 style='margin-bottom: 0;'>统一 AI 助手</h2>", unsafe_allow_html=True)
    st.caption("你的全能学习教练")
    st.write("")

    with st.container(border=True):
        st.markdown(
            f"**当前上下文:** {('已关联课程 #' + str(current_course_id)) if current_course_id else '未选择课程，当前可进行通用聊天'}"
        )
        st.markdown(f"**本轮状态:** {st.session_state.assistant_status_text}")
        policy_label = {
            "ask": "每次询问",
            "always_allow": "始终允许",
            "always_deny": "始终拒绝",
        }.get(permission_policy, "每次询问")
        st.caption(f"个人资料访问策略：{policy_label}")

    if pending_permission_reason and permission_policy == "ask":
        render_personal_context_permission_dialog(pending_permission_reason)

    # 历史消息完全依赖 session_state 渲染，这样用户发出消息后能立即看到自己的气泡。
    for message in st.session_state.assistant_messages:
        role = "assistant" if message.get("role") == "assistant" else "user"
        with st.chat_message(role):
            st.write(message.get("content") or "")
            if role == "assistant" and message.get("extra"):
                extra = message["extra"]
                if extra.get("mode"):
                    st.caption(f"模式：{extra.get('mode')}")

    if contexts:
        # 引用上下文默认折叠，既保留可解释性，又不打断主聊天流阅读。
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
