"""渲染课程详情页面，展示章节资源、作业、笔记和学习计划。"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

import streamlit as st


def render_course_detail_page(
    *,
    course: dict[str, Any] | None,
    enrollment: dict[str, Any] | None,
    chapters: list[dict[str, Any]],
    resources: list[dict[str, Any]],
    assignments: list[dict[str, Any]],
    notes: list[dict[str, Any]],
    plans: list[dict[str, Any]],
    progress_items: list[dict[str, Any]],
    can_edit_progress: bool,
    role_name: str,
) -> dict[str, Any] | None:
    if not course:
        st.warning("当前未选择课程，请先返回课程列表。")
        if st.button("返回课程列表", type="primary", use_container_width=True):
            return {"type": "back_to_courses"}
        return None

    st.markdown("<h2 style='margin-bottom: 0;'>课程详情</h2>", unsafe_allow_html=True)
    st.caption("查看课程信息、学习结构和当前学习概览")
    st.write("")

    chapter_resources: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for resource in resources:
        chapter_id = resource.get("chapter_id")
        if isinstance(chapter_id, int):
            chapter_resources[chapter_id].append(resource)

    # 把进度列表改造成按 `(类型, 目标 ID)` 查询的索引，后续渲染章节/资源/作业时可 O(1) 判断状态。
    progress_lookup = {
        (item.get("progress_type"), item.get("target_id")): item
        for item in progress_items
        if item.get("progress_type") and item.get("target_id") is not None
    }

    def is_completed(progress_type: str, target_id: Any) -> bool:
        item = progress_lookup.get((progress_type, target_id))
        return bool(item and item.get("progress_status") == "已完成")

    chapter_done = sum(1 for chapter in chapters if is_completed("chapter", chapter.get("chapter_id")))
    resource_done = sum(1 for resource in resources if is_completed("resource", resource.get("resource_id")))
    assignment_done = sum(1 for assignment in assignments if is_completed("assignment", assignment.get("assignment_id")))
    # 详情页与概览页保持相同口径，统一按三类学习项折算总体进度。
    total_items = len(chapters) + len(resources) + len(assignments)
    done_items = chapter_done + resource_done + assignment_done
    overall_progress = round((done_items / total_items) * 100, 1) if total_items else 0.0

    enrolled = enrollment is not None
    is_student = role_name == "学生"
    latest_note_time = notes[0].get("recorded_at") if notes else None
    latest_plan_time = plans[0].get("execute_time") if plans else None

    action_col1, action_col2, action_col3 = st.columns([1.2, 1.4, 1.6])
    with action_col1:
        if st.button("返回课程列表", use_container_width=True):
            return {"type": "back_to_courses"}
    with action_col2:
        if is_student:
            if enrolled:
                st.button("已选课", use_container_width=True, disabled=True)
            elif st.button("立即选课", type="primary", use_container_width=True):
                return {"type": "enroll"}
        elif role_name == "教师":
            st.button("授课课程", use_container_width=True, disabled=True)
        else:
            st.button("平台课程", use_container_width=True, disabled=True)
    with action_col3:
        if st.button("进入 AI 助手", use_container_width=True, type="secondary"):
            return {"type": "open_ai"}

    with st.container(border=True):
        st.subheader(course.get("course_name", "未命名课程"))
        if is_student:
            st.caption(
                f"课程 ID: {course.get('course_id')} | "
                f"上课时间: {course.get('class_time') or '未设置'} | "
                f"选课状态: {enrollment.get('enrollment_status') if enrollment else '未选课'}"
            )
        elif role_name == "教师":
            st.caption(
                f"课程 ID: {course.get('course_id')} | "
                f"上课时间: {course.get('class_time') or '未设置'} | 教师授课视角"
            )
        else:
            st.caption(
                f"课程 ID: {course.get('course_id')} | "
                f"上课时间: {course.get('class_time') or '未设置'} | 管理员查看视角"
            )
        st.write(course.get("course_intro") or "该课程暂未填写课程简介。")

    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
    metric_col1.metric("章节数", len(chapters))
    metric_col2.metric("资源数", len(resources))
    metric_col3.metric("作业数", len(assignments))
    metric_col4.metric("总进度", f"{overall_progress}%")

    summary_col1, summary_col2 = st.columns(2)
    with summary_col1:
        with st.container(border=True):
            st.markdown("**学习概览**")
            if is_student:
                st.write(f"已选课：{'是' if enrolled else '否'}")
            else:
                st.write(f"当前视角：{role_name}")
            st.write(f"章节完成：{chapter_done}/{len(chapters)}")
            st.write(f"资源完成：{resource_done}/{len(resources)}")
            st.write(f"作业完成：{assignment_done}/{len(assignments)}")
            st.write(f"课程笔记：{len(notes)} 条")
            st.write(f"最近笔记时间：{latest_note_time or '暂无'}")
            st.write(f"学习计划：{len(plans)} 条")
            st.write(f"最近计划时间：{latest_plan_time or '暂无'}")
    with summary_col2:
        with st.container(border=True):
            st.markdown("**建议动作**")
            if is_student and not enrolled:
                st.write("先完成选课，再进入课程学习和 AI 辅助学习。")
            elif is_student and overall_progress >= 100:
                st.write("本课程当前记录项已全部完成，可以进入 AI 助手复盘总结。")
            elif not chapters:
                st.write("该课程暂未配置章节内容，可以先查看作业和课程简介。")
            elif not is_student:
                st.write("可在课程管理页继续维护章节、资源、作业和课程通知。")
            else:
                st.write("建议按章节学习资源，并在完成后及时标记进度。")

    st.write("")
    st.markdown("### 章节与资源")
    if not chapters:
        st.info("当前课程还没有章节。")
    else:
        for chapter in chapters:
            chapter_id = chapter.get("chapter_id")
            items = chapter_resources.get(chapter_id, [])
            with st.container(border=True):
                title_col, action_col = st.columns([5, 1.5])
                with title_col:
                    st.markdown(
                        f"**第 {chapter.get('chapter_order') or '-'} 章：{chapter.get('chapter_title') or '未命名章节'}**"
                    )
                with action_col:
                    chapter_completed = is_completed("chapter", chapter_id)
                    if can_edit_progress and enrolled and chapter_id is not None:
                        if st.button(
                            "取消完成" if chapter_completed else "标记完成",
                            key=f"chapter-progress-{chapter_id}",
                            use_container_width=True,
                        ):
                            return {
                                "type": "toggle_progress",
                                "progress_type": "chapter",
                                "target_id": chapter_id,
                                "next_status": "未开始" if chapter_completed else "已完成",
                            }
                    else:
                        st.caption("已完成" if chapter_completed else "未完成")
                if chapter.get("chapter_content"):
                    st.write(chapter.get("chapter_content"))
                st.caption(f"资源数：{len(items)} | 状态：{'已完成' if chapter_completed else '未完成'}")
                if items:
                    for resource in items:
                        resource_id = resource.get("resource_id")
                        resource_completed = is_completed("resource", resource_id)
                        resource_col1, resource_col2 = st.columns([5, 1.5])
                        with resource_col1:
                            st.write(
                                f"- {resource.get('resource_title') or '未命名资源'}"
                                f"（{resource.get('resource_type') or '未标注类型'}）"
                            )
                        with resource_col2:
                            if can_edit_progress and enrolled and resource_id is not None:
                                if st.button(
                                    "取消完成" if resource_completed else "标记完成",
                                    key=f"resource-progress-{resource_id}",
                                    use_container_width=True,
                                ):
                                    return {
                                        "type": "toggle_progress",
                                        "progress_type": "resource",
                                        "target_id": resource_id,
                                        "next_status": "未开始" if resource_completed else "已完成",
                                    }
                            else:
                                st.caption("已完成" if resource_completed else "未完成")
                else:
                    st.write("暂无关联资源。")

    st.write("")
    st.markdown("### 作业概览")
    if not assignments:
        st.info("当前课程暂无作业。")
    else:
        for assignment in assignments:
            with st.container(border=True):
                assign_col1, assign_col2 = st.columns([5, 1.5])
                assignment_id = assignment.get("assignment_id")
                assignment_completed = is_completed("assignment", assignment_id)
                with assign_col1:
                    st.write(assignment.get("assignment_content") or "未填写作业内容")
                    st.caption(
                        f"截止时间：{assignment.get('due_at') or '未设置'} | "
                        f"状态：{'已完成' if assignment_completed else '未完成'}"
                    )
                with assign_col2:
                    if can_edit_progress and enrolled and assignment_id is not None:
                        if st.button(
                            "取消完成" if assignment_completed else "标记完成",
                            key=f"assignment-progress-{assignment_id}",
                            use_container_width=True,
                        ):
                            return {
                                "type": "toggle_progress",
                                "progress_type": "assignment",
                                "target_id": assignment_id,
                                "next_status": "未开始" if assignment_completed else "已完成",
                            }
                    else:
                        st.caption("已完成" if assignment_completed else "未完成")

    st.write("")
    st.markdown("### 笔记与学习计划")
    utility_col1, utility_col2 = st.columns(2)
    with utility_col1:
        with st.container(border=True):
            st.markdown("**课程笔记**")
            if not notes:
                st.info("你还没有在这门课程下记录笔记。")
            else:
                for note in notes[:5]:
                    st.write(note.get("content") or "")
                    st.caption(f"记录时间：{note.get('recorded_at') or '未知'}")
                    st.divider()
            if can_edit_progress and role_name == "学生":
                with st.form(f"course-detail-note-form-{course.get('course_id')}"):
                    new_note = st.text_area("快速记录笔记", placeholder="记录本节课的收获、疑问或待复习点...")
                    submitted = st.form_submit_button("保存课程笔记", type="primary", use_container_width=True)
                if submitted:
                    if not new_note.strip():
                        st.error("笔记内容不能为空。")
                    else:
                        return {
                            "type": "create_note",
                            "course_id": course.get("course_id"),
                            "content": new_note.strip(),
                        }
            if st.button("前往完整笔记页", key=f"open-notes-page-{course.get('course_id')}", use_container_width=True):
                return {"type": "open_notes_plans"}

    with utility_col2:
        with st.container(border=True):
            st.markdown("**学习计划**")
            if not plans:
                st.info("你还没有记录学习计划。")
            else:
                for plan in plans[:5]:
                    st.write(plan.get("plan_content") or "")
                    st.caption(
                        f"状态：{plan.get('plan_status') or '未开始'} | 执行时间：{plan.get('execute_time') or '未设置'}"
                    )
                    st.divider()
            if can_edit_progress and role_name == "学生":
                with st.form(f"course-detail-plan-form-{course.get('course_id')}"):
                    new_plan = st.text_input("快速新增学习计划", placeholder="例如：今晚完成本课程第 1 章复习")
                    submitted = st.form_submit_button("保存学习计划", type="primary", use_container_width=True)
                if submitted:
                    if not new_plan.strip():
                        st.error("学习计划不能为空。")
                    else:
                        return {
                            "type": "create_plan",
                            "plan_content": new_plan.strip(),
                            "plan_status": "未开始",
                        }

    return None
