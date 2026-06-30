"""渲染课程总览页面，展示课程卡片、学习进度与入口操作。"""

from __future__ import annotations

from typing import Any

import streamlit as st


def _render_course_grid(
    courses: list[dict[str, Any]],
    *,
    role_name: str,
    key_prefix: str,
    course_stats: dict[int, dict[str, int]],
    selected_course_id: int | None,
    enrolled_course_ids: set[int],
    progress_by_course: dict[int, float],
) -> None:
    if not courses:
        st.info("当前分类下还没有课程。")
        return

    cols = st.columns(2, gap="large")
    for index, course in enumerate(courses):
        with cols[index % 2]:
            with st.container(border=True):
                course_id = course.get("course_id")
                stats = course_stats.get(course_id, {"chapter_count": 0, "resource_count": 0})
                is_selected = selected_course_id == course_id
                is_enrolled = course_id in enrolled_course_ids if isinstance(course_id, int) else False
                progress = progress_by_course.get(course_id, 0.0) if isinstance(course_id, int) else 0.0

                st.subheader(course.get("course_name", "未命名课程"))
                if role_name == "学生":
                    st.caption(
                        f"课程 ID: {course_id} | {course.get('class_time') or '未设置上课时间'} | "
                        f"{'已选课' if is_enrolled else '未选课'} | "
                        f"{'当前查看中' if is_selected else '可查看详情'}"
                    )
                elif role_name == "教师":
                    st.caption(
                        f"课程 ID: {course_id} | {course.get('class_time') or '未设置上课时间'} | "
                        f"{'当前查看中' if is_selected else '授课课程'}"
                    )
                else:
                    st.caption(
                        f"课程 ID: {course_id} | {course.get('class_time') or '未设置上课时间'} | "
                        f"{'当前查看中' if is_selected else '课程详情'}"
                    )
                st.write(course.get("course_intro") or "该课程暂未填写简介。")

                c1, c2, c3 = st.columns(3)
                c1.metric("章节数", stats["chapter_count"])
                c2.metric("资源数", stats["resource_count"])
                if role_name == "学生":
                    c3.metric("进度", f"{progress}%")
                else:
                    c3.metric("作业数", stats["assignment_count"])

                if st.button(
                    "查看课程详情" if not is_selected else "继续当前课程",
                    key=f"{key_prefix}-course-open-{course_id}",
                    use_container_width=True,
                    type="primary" if is_selected else "secondary",
                ):
                    st.session_state.selected_course_id = course_id
                    st.session_state.current_page = "course_detail"
                    st.rerun()


def render_courses_page(
    courses: list[dict[str, Any]],
    *,
    user_info: dict[str, Any],
    course_stats: dict[int, dict[str, int]],
    selected_course_id: int | None,
    enrolled_course_ids: set[int],
    progress_by_course: dict[int, float],
    managed_course_ids: set[int] | None = None,
) -> None:
    role_name = user_info.get("role_name") or "学生"
    st.markdown("<h2 style='margin-bottom: 0;'>我的课程</h2>", unsafe_allow_html=True)
    if role_name == "学生":
        st.caption("查看课程安排，并按全部课程、已选课程和未选课程分类浏览")
    elif role_name == "教师":
        st.caption("查看你负责授课的课程，并进入课程详情或管理页面")
    else:
        st.caption("查看平台课程总览，并进入课程详情或管理页面")
    st.write("")

    search = st.text_input("🔍 按课程名称搜索", placeholder="输入课程名称...")
    filtered = [item for item in courses if search.lower() in str(item.get("course_name", "")).lower()]

    if not filtered:
        st.info("暂时还没有课程数据。")
        return

    if role_name == "学生":
        enrolled_courses = [item for item in filtered if item.get("course_id") in enrolled_course_ids]
        available_courses = [item for item in filtered if item.get("course_id") not in enrolled_course_ids]
        tab_all, tab_enrolled, tab_available = st.tabs(["全部课程", "已选课程", "未选课程"])
        with tab_all:
            _render_course_grid(
                filtered,
                role_name=role_name,
                key_prefix="all",
                course_stats=course_stats,
                selected_course_id=selected_course_id,
                enrolled_course_ids=enrolled_course_ids,
                progress_by_course=progress_by_course,
            )
        with tab_enrolled:
            _render_course_grid(
                enrolled_courses,
                role_name=role_name,
                key_prefix="enrolled",
                course_stats=course_stats,
                selected_course_id=selected_course_id,
                enrolled_course_ids=enrolled_course_ids,
                progress_by_course=progress_by_course,
            )
        with tab_available:
            _render_course_grid(
                available_courses,
                role_name=role_name,
                key_prefix="available",
                course_stats=course_stats,
                selected_course_id=selected_course_id,
                enrolled_course_ids=enrolled_course_ids,
                progress_by_course=progress_by_course,
            )
        return

    visible_courses = filtered
    if role_name == "教师" and managed_course_ids is not None:
        visible_courses = [item for item in filtered if item.get("course_id") in managed_course_ids]
    section_title = "授课课程" if role_name == "教师" else "全部课程"
    st.markdown(f"### {section_title}")
    _render_course_grid(
        visible_courses,
        role_name=role_name,
        key_prefix=section_title,
        course_stats=course_stats,
        selected_course_id=selected_course_id,
        enrolled_course_ids=enrolled_course_ids,
        progress_by_course=progress_by_course,
    )
