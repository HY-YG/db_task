"""Streamlit 前端入口，负责初始化状态、加载数据并分发页面渲染。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import streamlit as st

# 必须在最前面
st.set_page_config(page_title="智学空间", page_icon="🎓", layout="wide")

from frontend_streamlit.components.layout import inject_global_styles, render_side_navigation, render_topbar
from frontend_streamlit.pages.ai_assistant_page import render_ai_assistant_page
from frontend_streamlit.pages.assignments_page import render_assignments_page
from frontend_streamlit.pages.course_detail_page import render_course_detail_page
from frontend_streamlit.pages.course_management_page import render_course_management_page
from frontend_streamlit.pages.courses_page import render_courses_page
from frontend_streamlit.pages.inbox_page import render_inbox_page
from frontend_streamlit.pages.login_page import render_login_page
from frontend_streamlit.pages.notes_plans_page import render_notes_plans_page
from frontend_streamlit.pages.progress_dashboard_page import render_progress_dashboard_page
from frontend_streamlit.pages.user_management_page import render_user_management_page
from frontend_streamlit.services.api import (
    cached_get_assignment_dashboard,
    cached_get_course_detail_bundle,
    cached_get_course_management_bundle,
    cached_get_course_overview,
    cached_get_user,
    cached_list_notes,
    cached_list_roles,
    cached_list_study_plans,
    cached_list_users,
    clear_course_cache,
    clear_user_cache,
    clear_learning_cache,
    get_api_client,
    restore_api_result,
)
from frontend_streamlit.state import apply_query_params, init_state, login_user, reset_assistant_permission_state

api = get_api_client()
init_state()
apply_query_params()
inject_global_styles()


def load_user(user_id: int) -> dict[str, Any]:
    result = restore_api_result(cached_get_user(user_id))
    if result.ok and isinstance(result.data, dict):
        return result.data
    return {"user_id": user_id, "name": f"用户 {user_id}", "gender": "未设置", "age": 0, "role_id": None}


def load_users() -> list[dict[str, Any]]:
    result = restore_api_result(cached_list_users())
    if result.ok and isinstance(result.data, list):
        return [item for item in result.data if isinstance(item, dict)]
    return []


def load_roles() -> list[dict[str, Any]]:
    result = restore_api_result(cached_list_roles())
    if result.ok and isinstance(result.data, list):
        return [item for item in result.data if isinstance(item, dict)]
    return []


def enrich_user_info(user_info: dict[str, Any]) -> dict[str, Any]:
    role_map = {1: "学生", 2: "教师", 3: "管理员"}
    role_id = user_info.get("role_id")
    role_name = role_map.get(role_id, "学生")
    can_manage_courses = role_name in {"教师", "管理员"} or role_id in {2, 3}
    enriched = dict(user_info)
    enriched["role_name"] = role_name
    enriched["can_manage_courses"] = can_manage_courses
    return enriched


def load_course_overview(user_id: int) -> tuple[list[dict[str, Any]], dict[int, dict[str, int]], set[int], dict[int, float]]:
    overview_res = restore_api_result(cached_get_course_overview(user_id))
    payload = overview_res.data if overview_res.ok and isinstance(overview_res.data, dict) else {}
    items = payload.get("items") if isinstance(payload.get("items"), list) else []

    # 这里把接口返回拆成多个索引结构，后续页面渲染就不必反复遍历同一份列表。
    courses: list[dict[str, Any]] = []
    course_stats: dict[int, dict[str, int]] = {}
    enrolled_course_ids: set[int] = set()
    progress_by_course: dict[int, float] = {}

    for item in items:
        if not isinstance(item, dict):
            continue
        course = item.get("course")
        if not isinstance(course, dict):
            continue
        course_id = course.get("course_id")
        if not isinstance(course_id, int):
            continue
        courses.append(course)
        course_stats[course_id] = {
            "chapter_count": int(item.get("chapter_count") or 0),
            "resource_count": int(item.get("resource_count") or 0),
            "assignment_count": int(item.get("assignment_count") or 0),
        }
        progress_by_course[course_id] = float(item.get("progress_percent") or 0.0)
        if item.get("is_enrolled"):
            enrolled_course_ids.add(course_id)

    return courses, course_stats, enrolled_course_ids, progress_by_course


def load_management_bundle(user_info: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    bundle_user_id = st.session_state.current_user_id if user_info.get("role_name") == "教师" else None
    bundle_res = restore_api_result(cached_get_course_management_bundle(bundle_user_id))
    bundle = bundle_res.data if bundle_res.ok and isinstance(bundle_res.data, dict) else {}
    return {
        "courses": bundle.get("courses") if isinstance(bundle.get("courses"), list) else [],
        "chapters": bundle.get("chapters") if isinstance(bundle.get("chapters"), list) else [],
        "resources": bundle.get("resources") if isinstance(bundle.get("resources"), list) else [],
    }


def load_course_detail(course_id: int | None, user_id: int) -> dict[str, Any]:
    if course_id is None:
        return {
            "course": None,
            "enrollment": None,
            "chapters": [],
            "resources": [],
            "assignments": [],
            "notes": [],
            "plans": [],
            "progress_items": [],
        }

    detail_res = restore_api_result(cached_get_course_detail_bundle(course_id, user_id))
    payload = detail_res.data if detail_res.ok and isinstance(detail_res.data, dict) else {}
    notes = payload.get("notes") if isinstance(payload.get("notes"), list) else []
    # 后端返回的是“最近几条”，前端这里再按时间兜底排序，避免缓存恢复后顺序不稳定。
    notes.sort(key=lambda item: str(item.get("recorded_at") or ""), reverse=True)
    plans_res = restore_api_result(cached_list_study_plans(user_id))
    plans = plans_res.data if plans_res.ok and isinstance(plans_res.data, list) else []
    plans.sort(key=lambda item: str(item.get("execute_time") or ""), reverse=True)

    return {
        "course": payload.get("course") if isinstance(payload.get("course"), dict) else None,
        "enrollment": payload.get("enrollment") if isinstance(payload.get("enrollment"), dict) else None,
        "chapters": payload.get("chapters") if isinstance(payload.get("chapters"), list) else [],
        "resources": payload.get("resources") if isinstance(payload.get("resources"), list) else [],
        "assignments": payload.get("assignments") if isinstance(payload.get("assignments"), list) else [],
        "notes": notes,
        "plans": [item for item in plans if isinstance(item, dict)][:5],
        "progress_items": payload.get("progress_items") if isinstance(payload.get("progress_items"), list) else [],
    }


def load_assignment_dashboard(user_id: int, course_id: int | None) -> list[dict[str, Any]]:
    result = restore_api_result(cached_get_assignment_dashboard(user_id, course_id))
    payload = result.data if result.ok and isinstance(result.data, dict) else {}
    items = payload.get("items") if isinstance(payload.get("items"), list) else []
    return [item for item in items if isinstance(item, dict)]


def ensure_assistant_session() -> int | None:
    if st.session_state.assistant_session_id is not None:
        return st.session_state.assistant_session_id
    sessions_result = api.list_ai_sessions(user_id=st.session_state.current_user_id)
    sessions = sessions_result.data if sessions_result.ok and isinstance(sessions_result.data, list) else []
    latest_session = None
    for item in sessions:
        if isinstance(item, dict) and isinstance(item.get("session_id"), int):
            latest_session = item
    if isinstance(latest_session, dict):
        # 优先复用最近会话，这样刷新页面后还能接着上一轮聊天。
        st.session_state.assistant_session_id = latest_session.get("session_id")
        return st.session_state.assistant_session_id
    result = api.create_ai_session(user_id=st.session_state.current_user_id)
    if result.ok and isinstance(result.data, dict):
        st.session_state.assistant_session_id = result.data.get("session_id")
        return st.session_state.assistant_session_id
    return None


def hydrate_assistant_messages_from_backend() -> None:
    session_id = ensure_assistant_session()
    if session_id is None:
        return
    if st.session_state.assistant_messages:
        return
    result = api.list_ai_messages(session_id=session_id)
    items = result.data if result.ok and isinstance(result.data, list) else []
    restored_messages: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        sender = item.get("sender")
        payload = item.get("message_content")
        if not isinstance(payload, dict):
            continue
        text = payload.get("text")
        if not isinstance(text, str) or not text.strip():
            continue
        if sender == "user" and payload.get("type") in {"assistant_user", "assistant_permission_confirm"}:
            restored_messages.append({"role": "user", "content": text.strip()})
        elif sender == "ai" and payload.get("type") in {
            "assistant_answer",
            "assistant_permission_request",
            "assistant_coach_suggestion",
            "assistant_coach_started",
        }:
            # 前端聊天气泡只保留“对用户可见”的消息类型，过滤掉内部状态消息。
            restored_messages.append({"role": "assistant", "content": text.strip(), "extra": {"mode": payload.get("mode")}})
    st.session_state.assistant_messages = restored_messages


def build_status_text(payload: dict[str, Any]) -> str:
    mode = payload.get("mode")
    coach_stage = payload.get("coach_stage")
    if mode == "permission_request":
        return "本轮分析需要你的个人学习资料授权。"
    if mode == "coach_started":
        return f"学习教练已启动，当前阶段：{coach_stage or 'coach_diagnose'}。"
    if mode == "personal_analysis":
        return "已进入个性化学习分析模式。"
    if mode == "qa":
        return "本轮回答结合了课程资料上下文。"
    return "当前处于统一 AI 助手对话模式。"


def send_assistant_message(
    message: str,
    *,
    confirm_personal_context: bool = False,
    add_user_message: bool = True,
) -> None:
    session_id = ensure_assistant_session()
    if session_id is None:
        st.error("AI 会话创建失败，请先确认后端服务已启动。")
        return

    if add_user_message:
        st.session_state.assistant_messages.append({"role": "user", "content": message})

    result = api.assistant_chat(
        session_id=session_id,
        user_id=st.session_state.current_user_id,
        message=message,
        course_id=st.session_state.selected_course_id,
        confirm_personal_context=confirm_personal_context,
    )
    if not result.ok or not isinstance(result.data, dict):
        st.session_state.assistant_messages.append({"role": "assistant", "content": f"请求失败：{result.message or '未知错误'}"})
        return

    payload = result.data
    st.session_state.assistant_status_text = build_status_text(payload)
    st.session_state.assistant_contexts = payload.get("contexts", []) if isinstance(payload.get("contexts"), list) else []
    if payload.get("permission_required"):
        policy = st.session_state.get("assistant_permission_policy", "ask")
        st.session_state.pending_permission_request = True
        st.session_state.pending_permission_reason = payload.get("permission_reason")
        st.session_state.pending_permission_payload = {
            "message": message,
            "course_id": st.session_state.selected_course_id,
        }

        if confirm_personal_context:
            st.session_state.assistant_messages.append(
                {
                    "role": "assistant",
                    "content": "系统已尝试授权继续分析，但本次请求仍未完成。请稍后重试；若持续出现，请切换到“每次询问”模式后再试一次。",
                    "extra": {"mode": "permission_error"},
                }
            )
            return

        if policy == "always_allow":
            # 自动授权模式下不立刻递归调用，而是先把请求塞回 pending，交给 rerun 后统一执行。
            st.session_state.pending_permission_request = False
            st.session_state.pending_permission_reason = None
            st.session_state.assistant_pending_request = {
                "message": message,
                "confirm_personal_context": True,
                "course_id": st.session_state.selected_course_id,
            }
            return

        if policy == "always_deny":
            reset_assistant_permission_state()
            st.session_state.assistant_messages.append(
                {
                    "role": "assistant",
                    "content": "已按你的隐私设置拒绝读取个人学习资料。本次回答将不会使用你的笔记、学习计划和作业完成情况；如需启用，请到账号中心调整“AI 隐私授权”设置。",
                    "extra": {"mode": "privacy_denied"},
                }
            )
            return

        return

    reset_assistant_permission_state()
    st.session_state.assistant_messages.append(
        {
            "role": "assistant",
            "content": payload.get("answer") or "助手暂时没有返回内容。",
            "extra": {"mode": payload.get("mode"), "coach_stage": payload.get("coach_stage")},
        }
    )


def enqueue_assistant_request(message: str, *, confirm_personal_context: bool) -> None:
    # 采用“两段式渲染”：先立即显示用户消息，再在下一次 rerun 中真正请求后端。
    st.session_state.assistant_messages.append({"role": "user", "content": message})
    st.session_state.assistant_pending_request = {
        "message": message,
        "confirm_personal_context": confirm_personal_context,
    }


if st.session_state.current_user_id is None or not st.session_state.get("auth_token"):
    auth_action = render_login_page()
    if auth_action:
        if auth_action.get("type") == "login":
            auth_res = api.login(
                {
                    "username": auth_action.get("username"),
                    "password": auth_action.get("password"),
                }
            )
        else:
            auth_res = api.register(
                {
                    "username": auth_action.get("username"),
                    "password": auth_action.get("password"),
                    "name": auth_action.get("name"),
                    "gender": auth_action.get("gender"),
                    "age": auth_action.get("age"),
                    "role_name": auth_action.get("role_name"),
                }
            )
        payload = auth_res.data if auth_res.ok and isinstance(auth_res.data, dict) else {}
        raw_user_info = payload.get("userInfo")
        if not isinstance(raw_user_info, dict):
            raw_user_info = payload.get("user_info")
        user_info = raw_user_info if isinstance(raw_user_info, dict) else None
        token = payload.get("token")
        if auth_res.ok and user_info and isinstance(user_info.get("user_id"), int) and isinstance(token, str):
            clear_user_cache()
            login_user(int(user_info["user_id"]), token)
            st.rerun()
        else:
            st.error(f"认证失败：{auth_res.message or '请检查用户名和密码'}")
    st.stop()

user_info = enrich_user_info(load_user(st.session_state.current_user_id))

render_topbar(user_info)

st.write("")
st.write("")

left_col, right_col = st.columns([1.5, 6], gap="large")

with left_col:
    render_side_navigation(user_info)

with right_col:
    page = st.session_state.current_page

    if page == "courses":
        courses, course_stats, enrolled_course_ids, progress_by_course = load_course_overview(
            st.session_state.current_user_id
        )
        management_bundle = load_management_bundle(user_info) if user_info.get("can_manage_courses") else {
            "courses": [],
            "chapters": [],
            "resources": [],
        }
        managed_course_ids = {item.get("course_id") for item in management_bundle["courses"] if item.get("course_id") is not None}
        render_courses_page(
            courses,
            user_info=user_info,
            course_stats=course_stats,
            selected_course_id=st.session_state.selected_course_id,
            enrolled_course_ids=enrolled_course_ids,
            progress_by_course=progress_by_course,
            managed_course_ids=managed_course_ids,
        )

    elif page == "progress_dashboard":
        courses, course_stats, enrolled_course_ids, progress_by_course = load_course_overview(
            st.session_state.current_user_id
        )
        detail = load_course_detail(st.session_state.selected_course_id, st.session_state.current_user_id)
        action = render_progress_dashboard_page(
            courses=courses,
            course_stats=course_stats,
            enrolled_course_ids=enrolled_course_ids,
            progress_by_course=progress_by_course,
            selected_course_id=st.session_state.selected_course_id,
            detail=detail,
        )
        if action and action.get("type") == "select_course":
            st.session_state.selected_course_id = action.get("course_id")
            st.rerun()

    elif page == "course_management":
        bundle = load_management_bundle(user_info)
        render_course_management_page(
            user_info=user_info,
            courses=bundle["courses"],
            chapters=bundle["chapters"],
            resources=bundle["resources"],
        )

    elif page == "user_management":
        users = load_users()
        roles = load_roles()
        render_user_management_page(users=users, roles=roles)

    elif page == "course_detail":
        detail = load_course_detail(st.session_state.selected_course_id, st.session_state.current_user_id)
        action = render_course_detail_page(
            course=detail["course"],
            enrollment=detail["enrollment"],
            chapters=detail["chapters"],
            resources=detail["resources"],
            assignments=detail["assignments"],
            notes=detail["notes"],
            plans=detail["plans"],
            progress_items=detail["progress_items"],
            can_edit_progress=not user_info.get("can_manage_courses"),
            role_name=user_info.get("role_name") or "学生",
        )
        if action and action.get("type") == "back_to_courses":
            st.session_state.current_page = "courses"
            st.rerun()
        elif action and action.get("type") == "open_ai":
            if detail["course"] is None:
                st.error("当前课程不存在，无法进入 AI 助手。")
            else:
                st.session_state.current_page = "ai_assistant"
                st.rerun()
        elif action and action.get("type") == "enroll":
            if st.session_state.selected_course_id is not None:
                enroll_res = api.create_enrollment(
                    {
                        "user_id": st.session_state.current_user_id,
                        "course_id": st.session_state.selected_course_id,
                        "enrollment_status": "已选课",
                    }
                )
                if enroll_res.ok:
                    clear_course_cache()
                    st.success("选课成功，当前课程已加入你的学习空间。")
                    st.rerun()
                else:
                    st.error(f"选课失败：{enroll_res.message}")
        elif action and action.get("type") == "toggle_progress":
            if st.session_state.selected_course_id is not None:
                progress_res = api.upsert_progress(
                    {
                        "user_id": st.session_state.current_user_id,
                        "course_id": st.session_state.selected_course_id,
                        "progress_type": action["progress_type"],
                        "target_id": action["target_id"],
                        "progress_status": action["next_status"],
                    }
                )
                if progress_res.ok:
                    clear_course_cache()
                    st.success("学习进度已更新。")
                    st.rerun()
                else:
                    st.error(f"进度更新失败：{progress_res.message}")
        elif action and action.get("type") == "create_note":
            res = api.create_note(
                {
                    "user_id": st.session_state.current_user_id,
                    "course_id": action.get("course_id"),
                    "content": action.get("content"),
                }
            )
            if res.ok:
                clear_learning_cache()
                clear_course_cache()
                st.success("课程笔记已保存。")
                st.rerun()
            st.error(f"笔记保存失败：{res.message}")
        elif action and action.get("type") == "create_plan":
            res = api.create_study_plan(
                {
                    "user_id": st.session_state.current_user_id,
                    "plan_content": action.get("plan_content"),
                    "plan_status": action.get("plan_status") or "未开始",
                }
            )
            if res.ok:
                clear_learning_cache()
                st.success("学习计划已保存。")
                st.rerun()
            st.error(f"学习计划保存失败：{res.message}")
        elif action and action.get("type") == "open_notes_plans":
            st.session_state.current_page = "notes_plans"
            st.rerun()

    elif page == "inbox":
        notifs_res = api.list_notifications(user_id=st.session_state.current_user_id)
        notifications = notifs_res.data if notifs_res.ok and isinstance(notifs_res.data, list) else []
        inbox_action = render_inbox_page(notifications)
        if inbox_action:
            notification_id = inbox_action.get("notification_id")
            if not isinstance(notification_id, int):
                st.error("通知操作失败：通知 ID 无效。")
                st.stop()
            if inbox_action.get("type") == "mark_read":
                res = api.update_notification(notification_id, {"is_read": True})
                if res.ok:
                    clear_learning_cache()
                    st.success("通知已标记为已读。")
                    st.rerun()
                st.error(f"通知更新失败：{res.message}")
            elif inbox_action.get("type") == "delete":
                res = api.delete_notification(notification_id)
                if res.ok:
                    clear_learning_cache()
                    st.success("通知已删除。")
                    st.rerun()
                st.error(f"通知删除失败：{res.message}")

    elif page == "notes_plans":
        notes_res = restore_api_result(cached_list_notes(st.session_state.current_user_id, None))
        plans_res = restore_api_result(cached_list_study_plans(st.session_state.current_user_id))
        courses, _, enrolled_course_ids, _ = load_course_overview(st.session_state.current_user_id)
        notes = notes_res.data if notes_res.ok and isinstance(notes_res.data, list) else []
        plans = plans_res.data if plans_res.ok and isinstance(plans_res.data, list) else []
        available_courses = courses
        if not user_info.get("can_manage_courses"):
            available_courses = [item for item in courses if item.get("course_id") in enrolled_course_ids]

        payload = render_notes_plans_page(
            notes=notes,
            plans=plans,
            selected_course_id=st.session_state.selected_course_id,
            available_courses=available_courses,
        )
        if payload:
            if payload["type"] == "note":
                res = api.create_note(
                    {
                        "user_id": st.session_state.current_user_id,
                        "course_id": payload["course_id"],
                        "content": payload["content"],
                    }
                )
                if res.ok:
                    clear_learning_cache()
                    clear_course_cache()
                    st.session_state.selected_course_id = payload["course_id"]
                    st.success("笔记已保存")
                    st.rerun()
            elif payload["type"] == "plan":
                res = api.create_study_plan(
                    {
                        "user_id": st.session_state.current_user_id,
                        "plan_content": payload["plan_content"],
                        "plan_status": payload["plan_status"],
                    }
                )
                if res.ok:
                    clear_learning_cache()
                    st.success("学习计划已保存")
                    st.rerun()

    elif page == "assignments":
        courses, _, enrolled_course_ids, _ = load_course_overview(st.session_state.current_user_id)
        assignments = load_assignment_dashboard(st.session_state.current_user_id, st.session_state.selected_course_id)
        visible_courses = courses
        if user_info.get("role_name") == "教师":
            management_bundle = load_management_bundle(user_info)
            allowed_course_ids = {item.get("course_id") for item in management_bundle["courses"]}
            visible_courses = [item for item in courses if item.get("course_id") in allowed_course_ids]
            assignments = [
                item for item in assignments if (item.get("assignment") or {}).get("course_id") in allowed_course_ids
            ]
        elif not user_info.get("can_manage_courses"):
            visible_courses = [item for item in courses if item.get("course_id") in enrolled_course_ids]

        action = render_assignments_page(
            assignments=assignments,
            courses=visible_courses,
            selected_course_id=st.session_state.selected_course_id,
            can_submit=not user_info.get("can_manage_courses"),
        )
        if action and action.get("type") == "select_course":
            st.session_state.selected_course_id = action.get("course_id")
            st.rerun()
        elif action and action.get("type") == "submit_assignment":
            payload = {
                "user_id": st.session_state.current_user_id,
                "submission_status": "已提交",
                "submitted_at": datetime.now().isoformat(),
                "submission_content": action.get("content"),
            }
            submission_id = action.get("submission_id")
            if submission_id:
                submit_res = api.update_assignment_submission(int(submission_id), payload)
            else:
                submit_res = api.create_assignment_submission(int(action["assignment_id"]), payload)
            if submit_res.ok:
                progress_res = api.upsert_progress(
                    {
                        "user_id": st.session_state.current_user_id,
                        "course_id": action.get("course_id"),
                        "progress_type": "assignment",
                        "target_id": action.get("assignment_id"),
                        "progress_status": "已完成",
                    }
                )
                clear_course_cache()
                if progress_res.ok:
                    st.success("作业提交成功，作业进度已同步更新。")
                else:
                    st.warning("作业已提交，但进度同步失败，请稍后重试。")
                st.rerun()
            else:
                st.error(f"作业提交失败：{submit_res.message}")

    elif page == "ai_assistant":
        hydrate_assistant_messages_from_backend()
        message = render_ai_assistant_page(
            current_course_id=st.session_state.selected_course_id,
            contexts=st.session_state.assistant_contexts,
            pending_permission_reason=st.session_state.pending_permission_reason,
            permission_policy=st.session_state.get("assistant_permission_policy", "ask"),
        )
        permission_action = st.session_state.get("assistant_permission_dialog_action")
        if permission_action == "allow_once":
            pending_payload = st.session_state.get("pending_permission_payload") or {}
            reset_assistant_permission_state()
            st.session_state.assistant_pending_request = {
                "message": str(pending_payload.get("message") or ""),
                "confirm_personal_context": True,
                "course_id": pending_payload.get("course_id"),
            }
            st.rerun()
        elif permission_action == "always_allow":
            pending_payload = st.session_state.get("pending_permission_payload") or {}
            st.session_state.assistant_permission_policy = "always_allow"
            reset_assistant_permission_state()
            st.session_state.assistant_pending_request = {
                "message": str(pending_payload.get("message") or ""),
                "confirm_personal_context": True,
                "course_id": pending_payload.get("course_id"),
            }
            st.rerun()
        elif permission_action == "deny":
            reset_assistant_permission_state()
            st.session_state.assistant_messages.append(
                {
                    "role": "assistant",
                    "content": "本次已拒绝读取个人学习资料。我会继续基于公开课程信息回答；如果你希望我结合笔记和学习计划分析，请在系统授权提示中选择同意，或到账号中心修改授权策略。",
                    "extra": {"mode": "privacy_denied"},
                }
            )
            st.rerun()
        elif isinstance(message, str) and message.strip():
            enqueue_assistant_request(message.strip(), confirm_personal_context=False)
            st.rerun()

        pending = st.session_state.get("assistant_pending_request")
        if isinstance(pending, dict) and pending.get("message"):
            st.session_state.assistant_pending_request = None
            if pending.get("course_id") is not None:
                st.session_state.selected_course_id = pending.get("course_id")
            with st.spinner("AI 正在生成回复..."):
                send_assistant_message(
                    str(pending.get("message")),
                    confirm_personal_context=bool(pending.get("confirm_personal_context")),
                    add_user_message=False,
                )
            st.rerun()
