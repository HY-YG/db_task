"""渲染课程管理页面，处理课程、章节、资源与通知维护。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import streamlit as st

from frontend_streamlit.services.api import clear_course_cache, clear_learning_cache, get_api_client


def parse_due_at_input(value: str) -> str | None:
    raw = value.strip()
    if not raw:
        return None

    normalized = raw.replace("/", "-").replace("T", " ").replace("Z", "").strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            parsed = datetime.strptime(normalized, fmt)
            if fmt == "%Y-%m-%d":
                parsed = parsed.replace(hour=23, minute=59, second=0)
            return parsed.isoformat()
        except ValueError:
            continue
    return None


def render_course_management_page(
    *,
    user_info: dict[str, Any],
    courses: list[dict[str, Any]],
    chapters: list[dict[str, Any]],
    resources: list[dict[str, Any]],
) -> None:
    st.markdown("<h2 style='margin-bottom: 0;'>课程管理</h2>", unsafe_allow_html=True)
    st.caption("教师/管理员可在此创建课程、维护章节资源，并发布作业和课程通知")
    st.write("")

    if not user_info.get("can_manage_courses"):
        st.error("当前账号没有课程管理权限。")
        return

    api = get_api_client()
    course_options = {
        f"{course.get('course_name', '未命名课程')}（ID: {course.get('course_id')}）": course for course in courses
    }

    tab_course, tab_chapter, tab_resource, tab_assignment, tab_notification = st.tabs(
        ["课程", "章节", "资源", "作业发布", "通知发布"]
    )

    with tab_course:
        with st.container(border=True):
            st.subheader("创建课程")
            with st.form("create-course-form"):
                course_name = st.text_input("课程名称")
                class_time = st.text_input("上课时间", placeholder="例如：周二 3-4 节")
                course_intro = st.text_area("课程简介", placeholder="输入课程简介...")
                submitted = st.form_submit_button("创建课程", type="primary", use_container_width=True)
            if submitted:
                if not course_name.strip():
                    st.error("课程名称不能为空。")
                else:
                    res = api.create_course(
                        {
                            "course_name": course_name.strip(),
                            "class_time": class_time.strip() or None,
                            "course_intro": course_intro.strip() or None,
                            "teacher_user_id": user_info.get("user_id") if user_info.get("role_name") == "教师" else None,
                        }
                    )
                    if res.ok:
                        course_payload = res.data if isinstance(res.data, dict) else {}
                        created_course_id = course_payload.get("course_id")
                        if user_info.get("role_name") == "教师" and isinstance(created_course_id, int):
                            relation_res = api.create_teaching_relation(
                                {
                                    "user_id": user_info.get("user_id"),
                                    "course_id": created_course_id,
                                }
                            )
                            if not relation_res.ok:
                                st.error(f"课程已创建，但授课关系补写失败：{relation_res.message}")
                                st.stop()
                        clear_course_cache()
                        st.success("课程创建成功。")
                        st.rerun()
                    else:
                        st.error(f"课程创建失败：{res.message}")

        if course_options:
            with st.container(border=True):
                st.subheader("编辑课程")
                selected_label = st.selectbox("选择课程", options=list(course_options.keys()), key="manage-course-select")
                selected_course = course_options[selected_label]
                with st.form("update-course-form"):
                    update_name = st.text_input("课程名称", value=selected_course.get("course_name", ""))
                    update_time = st.text_input("上课时间", value=selected_course.get("class_time") or "")
                    update_intro = st.text_area("课程简介", value=selected_course.get("course_intro") or "")
                    updated = st.form_submit_button("保存课程修改", type="primary", use_container_width=True)
                if updated:
                    res = api.update_course(
                        selected_course["course_id"],
                        {
                            "course_name": update_name.strip() or None,
                            "class_time": update_time.strip() or None,
                            "course_intro": update_intro.strip() or None,
                        },
                    )
                    if res.ok:
                        clear_course_cache()
                        st.success("课程信息已更新。")
                        st.rerun()
                    else:
                        st.error(f"课程更新失败：{res.message}")
        else:
            st.info("当前还没有课程数据，请先创建课程。")

    with tab_chapter:
        if not course_options:
            st.info("请先创建课程，再维护章节。")
        else:
            selected_label = st.selectbox("选择要维护章节的课程", options=list(course_options.keys()), key="chapter-course-select")
            selected_course = course_options[selected_label]
            selected_course_id = selected_course["course_id"]
            course_chapters = [item for item in chapters if item.get("course_id") == selected_course_id]

            with st.container(border=True):
                st.subheader("新增章节")
                with st.form("create-chapter-form"):
                    chapter_title = st.text_input("章节标题")
                    chapter_order = st.number_input("章节顺序", min_value=1, step=1, value=max(len(course_chapters) + 1, 1))
                    chapter_content = st.text_area("章节内容", placeholder="输入章节说明...")
                    submitted = st.form_submit_button("创建章节", type="primary", use_container_width=True)
                if submitted:
                    if not chapter_title.strip():
                        st.error("章节标题不能为空。")
                    else:
                        res = api.create_chapter(
                            {
                                "course_id": selected_course_id,
                                "chapter_title": chapter_title.strip(),
                                "chapter_order": int(chapter_order),
                                "chapter_content": chapter_content.strip() or None,
                            }
                        )
                        if res.ok:
                            clear_course_cache()
                            st.success("章节创建成功。")
                            st.rerun()
                        else:
                            st.error(f"章节创建失败：{res.message}")

            if course_chapters:
                chapter_options = {
                    f"第 {item.get('chapter_order')} 章：{item.get('chapter_title')}（ID: {item.get('chapter_id')}）": item
                    for item in course_chapters
                }
                with st.container(border=True):
                    st.subheader("编辑章节")
                    chapter_label = st.selectbox("选择章节", options=list(chapter_options.keys()), key="update-chapter-select")
                    selected_chapter = chapter_options[chapter_label]
                    with st.form("update-chapter-form"):
                        update_title = st.text_input("章节标题", value=selected_chapter.get("chapter_title", ""))
                        update_order = st.number_input(
                            "章节顺序",
                            min_value=1,
                            step=1,
                            value=int(selected_chapter.get("chapter_order") or 1),
                        )
                        update_content = st.text_area("章节内容", value=selected_chapter.get("chapter_content") or "")
                        updated = st.form_submit_button("保存章节修改", type="primary", use_container_width=True)
                    if updated:
                        res = api.update_chapter(
                            selected_chapter["chapter_id"],
                            {
                                "chapter_title": update_title.strip() or None,
                                "chapter_order": int(update_order),
                                "chapter_content": update_content.strip() or None,
                            },
                        )
                        if res.ok:
                            clear_course_cache()
                            st.success("章节信息已更新。")
                            st.rerun()
                        else:
                            st.error(f"章节更新失败：{res.message}")
            else:
                st.info("当前课程还没有章节。")

    with tab_resource:
        if not chapters:
            st.info("请先创建章节，再维护资源。")
        else:
            chapter_options = {
                f"{item.get('chapter_title', '未命名章节')}（课程 {item.get('course_id')} / 章节ID {item.get('chapter_id')}）": item
                for item in chapters
            }
            chapter_label = st.selectbox("选择资源所属章节", options=list(chapter_options.keys()), key="resource-chapter-select")
            selected_chapter = chapter_options[chapter_label]
            selected_chapter_id = selected_chapter["chapter_id"]
            chapter_resources = [item for item in resources if item.get("chapter_id") == selected_chapter_id]

            with st.container(border=True):
                st.subheader("新增文本资源")
                with st.form("create-resource-form"):
                    resource_title = st.text_input("资源标题")
                    resource_type = st.text_input("资源类型", placeholder="例如：markdown / pdf / slide")
                    resource_content = st.text_area("资源内容或说明", placeholder="输入资源正文、链接或说明...")
                    submitted = st.form_submit_button("创建资源", type="primary", use_container_width=True)
                if submitted:
                    if not resource_title.strip():
                        st.error("资源标题不能为空。")
                    else:
                        res = api.create_resource(
                            {
                                "chapter_id": selected_chapter_id,
                                "resource_title": resource_title.strip(),
                                "resource_content": resource_content.strip() or None,
                                "resource_type": resource_type.strip() or None,
                            }
                        )
                        if res.ok:
                            clear_course_cache()
                            st.success("资源创建成功。")
                            st.rerun()
                        else:
                            st.error(f"资源创建失败：{res.message}")

            with st.container(border=True):
                st.subheader("上传文件资源")
                upload_title = st.text_input("上传后显示标题", key="upload-resource-title")
                version_description = st.text_input("版本说明", key="upload-version-desc")
                uploaded_file = st.file_uploader(
                    "选择资源文件",
                    key="resource-file-uploader",
                    type=None,
                    accept_multiple_files=False,
                )
                if st.button("上传并向量化资源", type="primary", use_container_width=True, key="upload-resource-btn"):
                    if uploaded_file is None:
                        st.error("请先选择文件。")
                    else:
                        res = api.upload_resource(
                            chapter_id=selected_chapter_id,
                            uploaded_file=uploaded_file,
                            resource_title=upload_title.strip() or None,
                            version_description=version_description.strip() or None,
                        )
                        if res.ok:
                            clear_course_cache()
                            st.success("文件资源上传成功，已触发向量化。")
                            st.rerun()
                        else:
                            st.error(f"资源上传失败：{res.message}")

            if chapter_resources:
                resource_options = {
                    f"{item.get('resource_title', '未命名资源')}（ID: {item.get('resource_id')}）": item
                    for item in chapter_resources
                }
                with st.container(border=True):
                    st.subheader("编辑资源")
                    resource_label = st.selectbox("选择资源", options=list(resource_options.keys()), key="update-resource-select")
                    selected_resource = resource_options[resource_label]
                    with st.form("update-resource-form"):
                        update_title = st.text_input("资源标题", value=selected_resource.get("resource_title", ""))
                        update_type = st.text_input("资源类型", value=selected_resource.get("resource_type") or "")
                        update_content = st.text_area("资源内容或说明", value=selected_resource.get("resource_content") or "")
                        updated = st.form_submit_button("保存资源修改", type="primary", use_container_width=True)
                    if updated:
                        res = api.update_resource(
                            selected_resource["resource_id"],
                            {
                                "resource_title": update_title.strip() or None,
                                "resource_type": update_type.strip() or None,
                                "resource_content": update_content.strip() or None,
                            },
                        )
                        if res.ok:
                            clear_course_cache()
                            st.success("资源信息已更新。")
                            st.rerun()
                        else:
                            st.error(f"资源更新失败：{res.message}")
            else:
                st.info("当前章节还没有资源。")

    with tab_assignment:
        if not course_options:
            st.info("请先创建课程，再发布作业。")
        else:
            selected_label = st.selectbox("选择发布作业的课程", options=list(course_options.keys()), key="assignment-course-select")
            selected_course = course_options[selected_label]
            selected_course_id = selected_course["course_id"]
            assignment_res = api.list_assignments(course_id=selected_course_id)
            assignment_items = assignment_res.data if assignment_res.ok and isinstance(assignment_res.data, list) else []

            with st.container(border=True):
                st.subheader("发布新作业")
                with st.form("create-assignment-form"):
                    assignment_content = st.text_area("作业内容", placeholder="输入作业要求、提交说明或评分标准...")
                    due_at = st.text_input(
                        "截止时间",
                        placeholder="例如：2026-07-10 23:59 或 2026-07-10T23:59:00",
                    )
                    submitted = st.form_submit_button("发布作业", type="primary", use_container_width=True)
                if submitted:
                    if not assignment_content.strip():
                        st.error("作业内容不能为空。")
                    else:
                        payload: dict[str, Any] = {
                            "course_id": selected_course_id,
                            "assignment_content": assignment_content.strip(),
                        }
                        if due_at.strip():
                            parsed_due_at = parse_due_at_input(due_at)
                            if parsed_due_at is None:
                                st.error("截止时间格式无效，请使用 YYYY-MM-DD、YYYY-MM-DD HH:MM 或 YYYY-MM-DDTHH:MM:SS。")
                                st.stop()
                            payload["due_at"] = parsed_due_at
                        res = api.create_assignment(payload)
                        if res.ok:
                            clear_course_cache()
                            st.success("作业发布成功。")
                            st.rerun()
                        else:
                            st.error(f"作业发布失败：{res.message}")

            if assignment_items:
                assignment_options = {
                    f"作业 {item.get('assignment_id')}": item
                    for item in assignment_items
                    if item.get("assignment_id") is not None
                }
                with st.container(border=True):
                    st.subheader("编辑作业")
                    assignment_label = st.selectbox(
                        "选择作业",
                        options=list(assignment_options.keys()),
                        key="update-assignment-select",
                    )
                    selected_assignment = assignment_options[assignment_label]
                    with st.form("update-assignment-form"):
                        update_content = st.text_area(
                            "作业内容",
                            value=selected_assignment.get("assignment_content") or "",
                        )
                        update_due_at = st.text_input(
                            "截止时间",
                            value=selected_assignment.get("due_at") or "",
                        )
                        updated = st.form_submit_button("保存作业修改", type="primary", use_container_width=True)
                    if updated:
                        parsed_update_due_at = parse_due_at_input(update_due_at) if update_due_at.strip() else None
                        if update_due_at.strip() and parsed_update_due_at is None:
                            st.error("截止时间格式无效，请使用 YYYY-MM-DD、YYYY-MM-DD HH:MM 或 YYYY-MM-DDTHH:MM:SS。")
                            st.stop()
                        payload = {
                            "assignment_content": update_content.strip() or None,
                            "due_at": parsed_update_due_at,
                        }
                        res = api.update_assignment(int(selected_assignment["assignment_id"]), payload)
                        if res.ok:
                            clear_course_cache()
                            st.success("作业信息已更新。")
                            st.rerun()
                        else:
                            st.error(f"作业更新失败：{res.message}")

                    delete_col, _ = st.columns([1, 2])
                    with delete_col:
                        if st.button(
                            "删除该作业",
                            key=f"delete-assignment-{selected_assignment['assignment_id']}",
                            use_container_width=True,
                        ):
                            res = api.delete_assignment(int(selected_assignment["assignment_id"]))
                            if res.ok:
                                clear_course_cache()
                                st.success("作业已删除。")
                                st.rerun()
                            else:
                                st.error(f"作业删除失败：{res.message}")

                submission_res = api.list_assignment_submissions(assignment_id=int(selected_assignment["assignment_id"]))
                submission_items = submission_res.data if submission_res.ok and isinstance(submission_res.data, list) else []
                if submission_items:
                    st.write("")
                    st.subheader("批改作业")
                    for submission in submission_items:
                        submission_id = submission.get("submission_id")
                        with st.container(border=True):
                            st.caption(
                                f"提交 ID: {submission_id} | 学生 ID: {submission.get('user_id')} | "
                                f"提交状态: {submission.get('submission_status') or '未提交'} | "
                                f"提交时间: {submission.get('submitted_at') or '未提交'}"
                            )
                            st.write(submission.get("submission_content") or "学生暂未填写提交内容。")
                            with st.form(f"review-submission-form-{submission_id}"):
                                score = st.number_input(
                                    "评分",
                                    min_value=0,
                                    max_value=100,
                                    value=int(submission.get("score") or 0),
                                    step=1,
                                    key=f"review-score-{submission_id}",
                                )
                                teacher_feedback = st.text_area(
                                    "批改反馈",
                                    value=submission.get("teacher_feedback") or "",
                                    key=f"review-feedback-{submission_id}",
                                )
                                reviewed = st.form_submit_button("保存批改", type="primary", use_container_width=True)
                            if reviewed:
                                res = api.update_assignment_submission(
                                    int(submission_id),
                                    {
                                        "submission_status": "已批改",
                                        "score": int(score),
                                        "teacher_feedback": teacher_feedback.strip() or None,
                                        "reviewed_at": datetime.now().isoformat(),
                                    },
                                )
                                if res.ok:
                                    clear_course_cache()
                                    st.success(f"提交 {submission_id} 已批改。")
                                    st.rerun()
                                else:
                                    st.error(f"批改失败：{res.message}")
                else:
                    st.info("该作业暂时还没有学生提交记录。")
            else:
                st.info("当前课程还没有作业。")

    with tab_notification:
        if not course_options:
            st.info("请先创建课程，再发布通知。")
        else:
            selected_label = st.selectbox("选择发布通知的课程", options=list(course_options.keys()), key="notification-course-select")
            selected_course = course_options[selected_label]
            with st.container(border=True):
                st.subheader("发布课程通知")
                with st.form("publish-notification-form"):
                    notification_content = st.text_area(
                        "通知内容",
                        placeholder="输入要发送给该课程学生的通知内容...",
                    )
                    submitted = st.form_submit_button("发布通知", type="primary", use_container_width=True)
                if submitted:
                    if not notification_content.strip():
                        st.error("通知内容不能为空。")
                    else:
                        res = api.publish_course_notification(
                            {
                                "sender_user_id": user_info.get("user_id"),
                                "course_id": selected_course["course_id"],
                                "notification_content": notification_content.strip(),
                            }
                        )
                        if res.ok and isinstance(res.data, dict):
                            clear_learning_cache()
                            st.success(f"课程通知已发布，已发送给 {res.data.get('sent_count', 0)} 名学生。")
                            st.rerun()
                        else:
                            st.error(f"通知发布失败：{res.message}")

            sent_notices_res = api.list_sent_course_notifications(
                sender_user_id=int(user_info.get("user_id") or 0),
                course_id=int(selected_course["course_id"]),
            )
            sent_notices = sent_notices_res.data if sent_notices_res.ok and isinstance(sent_notices_res.data, list) else []
            if sent_notices:
                st.write("")
                st.subheader("已发布通知")
                for idx, item in enumerate(sent_notices):
                    with st.container(border=True):
                        st.write(item.get("notification_content") or "")
                        st.caption(
                            f"发送时间: {item.get('sent_at')} | 接收学生数: {item.get('recipient_count', 0)}"
                        )
                        if st.button(
                            "删除该通知",
                            key=f"delete-course-notice-{selected_course['course_id']}-{idx}",
                            use_container_width=True,
                        ):
                            res = api.delete_course_notification_batch(
                                {
                                    "sender_user_id": user_info.get("user_id"),
                                    "course_id": selected_course["course_id"],
                                    "notification_content": item.get("notification_content"),
                                }
                            )
                            if res.ok:
                                clear_learning_cache()
                                st.success("该通知已从学生收件箱删除。")
                                st.rerun()
                            else:
                                st.error(f"通知删除失败：{res.message}")
            else:
                st.info("当前课程还没有已发布通知。")
