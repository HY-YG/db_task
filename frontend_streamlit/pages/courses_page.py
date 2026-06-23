from __future__ import annotations

from typing import Any

import streamlit as st


def render_courses_page(courses: list[dict[str, Any]]) -> None:
    st.markdown("<h2 style='margin-bottom: 0;'>我的课程</h2>", unsafe_allow_html=True)
    st.caption("课程空间")
    st.write("")

    search = st.text_input("🔍 按课程名称搜索", placeholder="输入课程名称...")
    filtered = [item for item in courses if search.lower() in str(item.get("course_name", "")).lower()]

    if not filtered:
        st.info("暂时还没有课程数据。")
        return

    cols = st.columns(2, gap="large")
    for index, course in enumerate(filtered):
        with cols[index % 2]:
            with st.container(border=True):
                st.subheader(course.get("course_name", "未命名课程"))
                st.caption(f"课程 ID: {course.get('course_id')} | {course.get('class_time') or '未设置上课时间'}")
                st.write(course.get("course_intro") or "暂无课程简介")

                c1, c2 = st.columns(2)
                c1.metric("章节", "0")
                c2.metric("资源", "0")

                if st.button("进入该课程", key=f"course-open-{course.get('course_id')}", use_container_width=True):
                    st.session_state.selected_course_id = course.get("course_id")
                    st.session_state.current_page = "ai_assistant"
                    st.rerun()
