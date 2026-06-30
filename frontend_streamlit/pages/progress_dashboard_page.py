"""渲染学习进度看板页面，聚合课程进度与完成情况。"""

from __future__ import annotations

from collections import Counter
from typing import Any

import streamlit as st


def render_progress_dashboard_page(
    *,
    courses: list[dict[str, Any]],
    course_stats: dict[int, dict[str, int]],
    enrolled_course_ids: set[int],
    progress_by_course: dict[int, float],
    selected_course_id: int | None,
    detail: dict[str, Any] | None,
) -> dict[str, Any] | None:
    st.markdown("<h2 style='margin-bottom: 0;'>学习进度看板</h2>", unsafe_allow_html=True)
    st.caption("聚合查看课程完成率、当前课程结构进度和最近完成情况")
    st.write("")

    enrolled_courses = [item for item in courses if item.get("course_id") in enrolled_course_ids]
    if not enrolled_courses:
        st.info("你还没有已选课程，先去课程页选课后，这里会显示学习进度。")
        return None

    avg_progress = round(
        sum(progress_by_course.get(item.get("course_id"), 0.0) for item in enrolled_courses) / len(enrolled_courses),
        1,
    )
    completed_courses = sum(1 for item in enrolled_courses if progress_by_course.get(item.get("course_id"), 0.0) >= 100)

    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
    metric_col1.metric("已选课程", len(enrolled_courses))
    metric_col2.metric("平均进度", f"{avg_progress}%")
    metric_col3.metric("已完成课程", completed_courses)
    metric_col4.metric("当前课程", selected_course_id or "未选择")

    course_options = {"当前选中课程": selected_course_id}
    for course in enrolled_courses:
        course_id = course.get("course_id")
        if isinstance(course_id, int):
            course_options[f"{course.get('course_name', '未命名课程')}（ID: {course_id}）"] = course_id

    selected_label = st.selectbox("查看课程进度", options=list(course_options.keys()), key="progress-dashboard-course")
    selected_option_course_id = course_options[selected_label]
    if selected_option_course_id != selected_course_id:
        return {"type": "select_course", "course_id": selected_option_course_id}

    st.write("")
    st.markdown("### 课程总览")
    for course in enrolled_courses:
        course_id = course.get("course_id")
        stats = course_stats.get(course_id, {"chapter_count": 0, "resource_count": 0, "assignment_count": 0})
        progress = float(progress_by_course.get(course_id, 0.0))
        with st.container(border=True):
            st.write(f"**{course.get('course_name', '未命名课程')}**")
            st.caption(
                f"课程 ID: {course_id} | "
                f"章节 {stats.get('chapter_count', 0)} | 资源 {stats.get('resource_count', 0)} | 作业 {stats.get('assignment_count', 0)}"
            )
            st.progress(min(max(progress / 100, 0.0), 1.0), text=f"当前完成率 {progress}%")

    if not detail or not detail.get("course"):
        st.info("请选择一门课程后，这里会展示章节、资源和作业的详细进度拆解。")
        return None

    progress_items = detail.get("progress_items") if isinstance(detail.get("progress_items"), list) else []
    progress_counter = Counter(
        item.get("progress_type")
        for item in progress_items
        if item.get("progress_status") == "已完成" and item.get("progress_type") in {"chapter", "resource", "assignment"}
    )
    chapter_total = len(detail.get("chapters") or [])
    resource_total = len(detail.get("resources") or [])
    assignment_total = len(detail.get("assignments") or [])

    st.write("")
    st.markdown("### 当前课程拆解")
    breakdown_col1, breakdown_col2, breakdown_col3 = st.columns(3)
    breakdown_col1.metric("章节完成", f"{progress_counter.get('chapter', 0)}/{chapter_total}")
    breakdown_col2.metric("资源完成", f"{progress_counter.get('resource', 0)}/{resource_total}")
    breakdown_col3.metric("作业完成", f"{progress_counter.get('assignment', 0)}/{assignment_total}")

    recent_completed = [
        item
        for item in progress_items
        if item.get("progress_status") == "已完成" and item.get("completed_at")
    ]
    recent_completed.sort(key=lambda item: str(item.get("completed_at") or ""), reverse=True)

    st.write("")
    st.markdown("### 最近完成记录")
    if not recent_completed:
        st.info("当前课程还没有已完成记录。")
    else:
        for item in recent_completed[:8]:
            with st.container(border=True):
                st.write(
                    f"{item.get('progress_type', 'unknown')} #{item.get('target_id')} 已完成"
                )
                st.caption(f"完成时间：{item.get('completed_at')}")

    return None
