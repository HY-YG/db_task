"""渲染消息收件箱页面，展示通知并处理已读与删除操作。"""

from __future__ import annotations

from typing import Any

import streamlit as st


def render_inbox_page(notifications: list[dict[str, Any]]) -> dict[str, Any] | None:
    st.markdown("<h2 style='margin-bottom: 0;'>收件箱</h2>", unsafe_allow_html=True)
    st.caption("系统通知与消息")
    st.write("")

    if not notifications:
        st.info("还没有通知消息。")
        return None

    for notif in notifications:
        with st.container(border=True):
            notification_id = notif.get("notification_id")
            st.markdown(f"**通知 ID: {notification_id}**")
            st.write(notif.get("notification_content", ""))
            st.caption(f"发送时间: {notif.get('sent_at')} | 已读: {'是' if notif.get('is_read') else '否'}")
            cols = st.columns(2)
            with cols[0]:
                if not notif.get("is_read") and st.button(
                    "标记已读",
                    key=f"notif-read-{notification_id}",
                    use_container_width=True,
                ):
                    return {"type": "mark_read", "notification_id": notification_id}
            with cols[1]:
                if st.button(
                    "删除通知",
                    key=f"notif-delete-{notification_id}",
                    use_container_width=True,
                ):
                    return {"type": "delete", "notification_id": notification_id}
    return None
