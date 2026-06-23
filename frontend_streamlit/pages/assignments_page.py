from __future__ import annotations

from typing import Any

import streamlit as st


def render_assignments_page(assignments: list[dict[str, Any]]) -> None:
    st.markdown("<h2 style='margin-bottom: 0;'>作业</h2>", unsafe_allow_html=True)
    st.caption("当前课程作业列表")
    st.write("")

    if not assignments:
        st.info("当前课程没有作业。")
        return

    for assign in assignments:
        with st.container(border=True):
            st.markdown(f"**作业 ID: {assign.get('assignment_id')}**")
            st.write(assign.get("assignment_content", ""))
            st.caption(f"截止时间: {assign.get('due_at') or '未设置'}")
