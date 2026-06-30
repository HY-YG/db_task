"""渲染作业页面，处理筛选、提交、批改结果展示等交互。"""

from __future__ import annotations

from typing import Any

import streamlit as st


def render_assignments_page(
    *,
    assignments: list[dict[str, Any]],
    courses: list[dict[str, Any]],
    selected_course_id: int | None,
    can_submit: bool,
) -> dict[str, Any] | None:
    st.markdown("<h2 style='margin-bottom: 0;'>作业提交</h2>", unsafe_allow_html=True)
    st.caption("查看作业要求、提交内容，并追踪每项作业的提交状态")
    st.write("")

    course_options = {"全部课程": None}
    for course in courses:
        course_id = course.get("course_id")
        if isinstance(course_id, int):
            course_options[f"{course.get('course_name', '未命名课程')}（ID: {course_id}）"] = course_id
    labels = list(course_options.keys())
    default_index = 0
    for idx, label in enumerate(labels):
        if course_options[label] == selected_course_id:
            default_index = idx
            break
    selected_label = st.selectbox("课程筛选", options=labels, index=default_index, key="assignment-course-filter")
    chosen_course_id = course_options[selected_label]
    if chosen_course_id != selected_course_id:
        return {"type": "select_course", "course_id": chosen_course_id}

    if not assignments:
        st.info("当前筛选条件下没有作业。")
        return None

    for item in assignments:
        assignment = item.get("assignment") if isinstance(item.get("assignment"), dict) else {}
        course = item.get("course") if isinstance(item.get("course"), dict) else {}
        submission = item.get("submission") if isinstance(item.get("submission"), dict) else None
        assignment_id = assignment.get("assignment_id")
        progress_status = item.get("progress_status") or "未开始"
        submission_status = submission.get("submission_status") if submission else "未提交"
        existing_content = submission.get("submission_content") if submission else ""
        teacher_feedback = submission.get("teacher_feedback") if submission else None
        score = submission.get("score") if submission else None
        is_enrolled = bool(item.get("is_enrolled"))
        with st.container(border=True):
            st.markdown(f"**作业 ID: {assignment_id}**")
            st.write(assignment.get("assignment_content", ""))
            st.caption(
                f"所属课程：{course.get('course_name') or '未知课程'} | "
                f"截止时间：{assignment.get('due_at') or '未设置'} | "
                f"提交状态：{submission_status} | "
                f"学习进度：{progress_status}"
            )
            if submission and (teacher_feedback or score is not None):
                st.info(
                    f"批改结果：分数 {score if score is not None else '未评分'} | "
                    f"反馈：{teacher_feedback or '暂无反馈'}"
                )
            if not can_submit:
                st.info("当前账号为教师/管理员，此处展示作业概览；如需发布或编辑作业，请前往“课程管理”。")
                continue
            if not is_enrolled:
                st.warning("你还没有选修该课程，暂时不能提交作业。")
                continue
            with st.form(f"assignment-submit-form-{assignment_id}"):
                content = st.text_area(
                    "提交内容",
                    value=existing_content or "",
                    key=f"assignment-submit-content-{assignment_id}",
                    placeholder="输入你的作业答案、总结或提交说明...",
                )
                submitted = st.form_submit_button(
                    "更新提交" if submission else "提交作业",
                    type="primary",
                    use_container_width=True,
                )
            if submitted:
                if not str(content).strip():
                    st.error("提交内容不能为空。")
                else:
                    return {
                        "type": "submit_assignment",
                        "assignment_id": assignment_id,
                        "submission_id": submission.get("submission_id") if submission else None,
                        "content": str(content).strip(),
                        "course_id": assignment.get("course_id"),
                    }
    return None
