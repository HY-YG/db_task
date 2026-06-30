"""渲染登录注册页面，收集认证表单并返回用户操作结果。"""

from __future__ import annotations

import streamlit as st


def render_login_page() -> dict[str, str | int | None] | None:
    st.markdown("<h2 style='margin-bottom: 0;'>登录智学空间</h2>", unsafe_allow_html=True)
    st.caption("请选择登录或注册。注册账号时仅支持学生和教师身份。")
    st.write("")

    tab_login, tab_register = st.tabs(["登录", "注册"])

    with tab_login:
        with st.form("login-form"):
            username = st.text_input("用户名", placeholder="输入用户名")
            password = st.text_input("密码", type="password", placeholder="输入密码")
            submitted = st.form_submit_button("登录", type="primary", use_container_width=True)
        if submitted:
            if not username.strip() or not password:
                st.error("请输入用户名和密码。")
            else:
                return {
                    "type": "login",
                    "username": username.strip(),
                    "password": password,
                }
        st.info("默认管理员账号：admin / admin123456")

    with tab_register:
        with st.form("register-form"):
            name = st.text_input("姓名", placeholder="输入你的姓名")
            username = st.text_input("用户名", placeholder="3-50 位用户名")
            gender = st.selectbox("性别", options=["未设置", "男", "女"])
            age = st.number_input("年龄", min_value=0, max_value=150, value=18)
            role_name = st.radio("注册身份", options=["学生", "教师"], horizontal=True)
            password = st.text_input("密码", type="password", placeholder="至少 6 位")
            confirm_password = st.text_input("确认密码", type="password", placeholder="再次输入密码")
            submitted = st.form_submit_button("注册并进入系统", type="primary", use_container_width=True)
        if submitted:
            if not name.strip() or not username.strip():
                st.error("姓名和用户名不能为空。")
            elif len(password) < 6:
                st.error("密码至少需要 6 位。")
            elif password != confirm_password:
                st.error("两次输入的密码不一致。")
            else:
                return {
                    "type": "register",
                    "name": name.strip(),
                    "username": username.strip(),
                    "gender": None if gender == "未设置" else gender,
                    "age": int(age),
                    "role_name": role_name,
                    "password": password,
                }
    return None
