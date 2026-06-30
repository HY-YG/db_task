"""渲染笔记与学习计划页面，支持查看与新增学习记录。"""

from __future__ import annotations

from typing import Any

import streamlit as st


def render_notes_plans_page(
    notes: list[dict[str, Any]],
    plans: list[dict[str, Any]],
    selected_course_id: int | None,
    available_courses: list[dict[str, Any]],
) -> dict[str, Any] | None:
    st.markdown("<h2 style='margin-bottom: 0;'>笔记与学习计划</h2>", unsafe_allow_html=True)
    st.caption("管理你的学习进度与心得")
    st.write("")

    tab1, tab2 = st.tabs(["📝 笔记", "🎯 学习计划"])

    payload = None

    with tab1:
        course_options = {
            f"{course.get('course_name') or '未命名课程'}（ID: {course.get('course_id')}）": course
            for course in available_courses
            if isinstance(course.get("course_id"), int)
        }
        active_course_id = selected_course_id
        if course_options:
            option_labels = list(course_options.keys())
            default_index = 0
            if isinstance(selected_course_id, int):
                for index, label in enumerate(option_labels):
                    if course_options[label].get("course_id") == selected_course_id:
                        default_index = index
                        break
            selected_label = st.selectbox("选择笔记所属课程", options=option_labels, index=default_index)
            active_course_id = course_options[selected_label].get("course_id")
        else:
            st.warning("当前没有可选课程，请先去课程页选择或加入课程。")

        new_note = st.text_area("新增笔记", placeholder="记录你的学习心得...")
        if st.button("保存笔记", type="primary"):
            if not isinstance(active_course_id, int):
                st.error("请先选择一门课程。")
            elif new_note.strip():
                payload = {"type": "note", "course_id": active_course_id, "content": new_note.strip()}
            else:
                st.error("笔记内容不能为空")

        st.divider()
        filtered_notes = [
            note for note in notes if not isinstance(active_course_id, int) or note.get("course_id") == active_course_id
        ]
        if not filtered_notes:
            st.info("暂无笔记。")
        for note in filtered_notes:
            with st.container(border=True):
                st.caption(f"课程 ID: {note.get('course_id')} | 时间: {note.get('recorded_at')}")
                st.write(note.get("content", ""))

    with tab2:
        new_plan = st.text_input("新增学习计划", placeholder="例如：本周完成第八周的作业")
        if st.button("保存计划", type="primary"):
            if new_plan.strip():
                payload = {"type": "plan", "plan_content": new_plan.strip(), "plan_status": "未开始"}
            else:
                st.error("计划内容不能为空")

        st.divider()
        if not plans:
            st.info("暂无学习计划。")
        for plan in plans:
            with st.container(border=True):
                st.caption(f"状态: {plan.get('plan_status')} | 执行时间: {plan.get('execute_time') or '未设置'}")
                st.write(plan.get("plan_content", ""))

    return payload
