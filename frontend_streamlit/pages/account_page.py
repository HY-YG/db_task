from __future__ import annotations

import time

import streamlit as st

from frontend_streamlit.services.api import ApiClient


@st.dialog("账号中心", width="large")
def render_account_dialog(user_info: dict) -> None:
    tab1, tab2, tab3, tab4 = st.tabs(["基本资料", "修改头像", "密码管理", "注销账号"])

    with tab1:
        st.subheader("基本资料")
        name = st.text_input("姓名", value=user_info.get("name", ""))
        gender_options = ["男", "女", "未设置"]
        current_gender = user_info.get("gender", "未设置")
        if current_gender not in gender_options:
            current_gender = "未设置"

        gender = st.selectbox("性别", options=gender_options, index=gender_options.index(current_gender))
        age = st.number_input("年龄", min_value=0, max_value=150, value=int(user_info.get("age") or 0))

        if st.button("保存修改", type="primary", use_container_width=True):
            api = ApiClient()
            res = api.update_user(user_info.get("user_id", 1), {"name": name, "gender": gender, "age": age})
            if res.ok:
                st.success("基础资料已更新！")
                time.sleep(1)
                st.rerun()
            else:
                st.error(f"更新失败：{res.message}")

    with tab2:
        st.info("头像修改功能暂未开放")
    with tab3:
        st.info("密码管理功能暂未开放")
    with tab4:
        st.warning("注销账号功能暂未开放")
