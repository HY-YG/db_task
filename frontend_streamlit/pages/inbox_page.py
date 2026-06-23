from __future__ import annotations

from typing import Any

import streamlit as st


def render_inbox_page(notifications: list[dict[str, Any]]) -> None:
    st.markdown("<h2 style='margin-bottom: 0;'>收件箱</h2>", unsafe_allow_html=True)
    st.caption("系统通知与消息")
    st.write("")

    if not notifications:
        st.info("还没有通知消息。")
        return

    for notif in notifications:
        with st.container(border=True):
            st.markdown(f"**通知 ID: {notif.get('notification_id')}**")
            st.write(notif.get("notification_content", ""))
            st.caption(f"发送时间: {notif.get('sent_at')} | 已读: {'是' if notif.get('is_read') else '否'}")
