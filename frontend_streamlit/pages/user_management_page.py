"""渲染用户管理页面，供管理员维护用户与角色信息。"""

from __future__ import annotations

from typing import Any

import streamlit as st

from frontend_streamlit.services.api import clear_user_cache, get_api_client


def render_user_management_page(
    *,
    users: list[dict[str, Any]],
    roles: list[dict[str, Any]],
) -> None:
    st.markdown("<h2 style='margin-bottom: 0;'>用户管理</h2>", unsafe_allow_html=True)
    st.caption("管理员可在此查看用户、调整角色和启用状态")
    st.write("")

    if not users:
        st.info("当前还没有用户数据。")
        return

    role_map = {item.get("role_id"): item.get("role_name") for item in roles if item.get("role_id") is not None}
    for item in users:
        item["role_name"] = role_map.get(item.get("role_id"), "未知角色")

    user_options = {
        f"{item.get('name', '未命名用户')}（{item.get('username') or '未设置用户名'}）": item
        for item in users
        if item.get("user_id") is not None
    }
    selected_label = st.selectbox("选择用户", options=list(user_options.keys()), key="admin-user-select")
    selected_user = user_options[selected_label]
    api = get_api_client()

    with st.container(border=True):
        st.write(f"用户 ID：{selected_user.get('user_id')}")
        st.write(f"当前角色：{selected_user.get('role_name')}")
        st.write(f"创建时间：{selected_user.get('created_at') or '未知'}")

    role_options = {
        f"{item.get('role_name')}（ID: {item.get('role_id')}）": item.get("role_id")
        for item in roles
        if item.get("role_id") is not None
    }
    role_labels = list(role_options.keys())
    default_role_index = 0
    for idx, label in enumerate(role_labels):
        if role_options[label] == selected_user.get("role_id"):
            default_role_index = idx
            break

    with st.form("admin-update-user-form"):
        name = st.text_input("姓名", value=selected_user.get("name") or "")
        username = st.text_input("用户名", value=selected_user.get("username") or "")
        gender = st.selectbox(
            "性别",
            options=["未设置", "男", "女"],
            index=["未设置", "男", "女"].index(selected_user.get("gender") or "未设置")
            if (selected_user.get("gender") or "未设置") in {"未设置", "男", "女"}
            else 0,
        )
        age = st.number_input("年龄", min_value=0, max_value=150, value=int(selected_user.get("age") or 0))
        role_label = st.selectbox("角色", options=role_labels, index=default_role_index)
        is_active = st.checkbox("账号可用", value=bool(selected_user.get("is_active", True)))
        submitted = st.form_submit_button("保存用户修改", type="primary", use_container_width=True)

    if submitted:
        res = api.update_user(
            int(selected_user["user_id"]),
            {
                "name": name.strip() or None,
                "username": username.strip() or None,
                "gender": None if gender == "未设置" else gender,
                "age": int(age),
                "role_id": role_options[role_label],
                "is_active": is_active,
            },
        )
        if res.ok:
            clear_user_cache()
            st.success("用户信息已更新。")
            st.rerun()
        else:
            st.error(f"用户更新失败：{res.message}")
