"""渲染账号中心页面，处理个人信息、密码与隐私授权配置。"""

from __future__ import annotations

import streamlit as st

from frontend_streamlit.services.api import clear_user_cache, get_api_client


@st.dialog("账号中心", width="large")
def render_account_dialog(user_info: dict) -> None:
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["基本资料", "修改头像", "密码管理", "AI 隐私授权", "注销账号"])

    with tab1:
        st.subheader("基本资料")
        st.caption(
            f"用户 ID: {user_info.get('user_id')} | "
            f"角色 ID: {user_info.get('role_id') or '未分配'} | "
            f"用户名: {user_info.get('username') or '未设置'}"
        )
        name = st.text_input("姓名", value=user_info.get("name", ""))
        gender_options = ["男", "女", "未设置"]
        current_gender = user_info.get("gender", "未设置")
        if current_gender not in gender_options:
            current_gender = "未设置"

        gender = st.selectbox("性别", options=gender_options, index=gender_options.index(current_gender))
        age = st.number_input("年龄", min_value=0, max_value=150, value=int(user_info.get("age") or 0))

        if st.button("保存修改", type="primary", use_container_width=True):
            api = get_api_client()
            res = api.update_user(user_info.get("user_id", 1), {"name": name, "gender": gender, "age": age})
            if res.ok:
                clear_user_cache()
                st.success("基础资料已更新！")
                st.rerun()
            else:
                st.error(f"更新失败：{res.message}")

    with tab2:
        st.info("当前版本尚未接入头像上传接口。")
    with tab3:
        old_password = st.text_input("旧密码", type="password", key="account-old-password")
        new_password = st.text_input("新密码", type="password", key="account-new-password")
        confirm_password = st.text_input("确认新密码", type="password", key="account-confirm-password")
        if st.button("修改密码", type="primary", use_container_width=True):
            if len(new_password) < 6:
                st.error("新密码至少需要 6 位。")
            elif new_password != confirm_password:
                st.error("两次输入的新密码不一致。")
            else:
                api = get_api_client()
                res = api.change_password(
                    {
                        "old_password": old_password,
                        "new_password": new_password,
                    }
                )
                if res.ok:
                    st.success("密码修改成功。")
                else:
                    st.error(f"密码修改失败：{res.message}")
    with tab4:
        st.subheader("AI 个人资料访问")
        st.caption("控制 AI 在需要做个性化分析时，是否可以读取你的笔记、学习计划和作业完成情况。")

        policy_options = {
            "每次询问": "ask",
            "始终允许": "always_allow",
            "始终拒绝": "always_deny",
        }
        current_policy = st.session_state.get("assistant_permission_policy", "ask")
        reverse_map = {value: key for key, value in policy_options.items()}
        selected_label = st.radio(
            "访问策略",
            options=list(policy_options.keys()),
            index=list(policy_options.keys()).index(reverse_map.get(current_policy, "每次询问")),
            help="“始终允许”会在 AI 需要个人学习资料时自动继续分析，不再弹出授权提示。",
        )
        active_policy = policy_options[selected_label]
        st.session_state.assistant_permission_policy = active_policy

        if active_policy == "always_allow":
            st.success("当前为始终允许模式，AI 在需要私人学习资料时会直接继续分析。")
        elif active_policy == "always_deny":
            st.warning("当前为始终拒绝模式，AI 将只基于公开课程资料进行回答。")
        else:
            st.info("当前为每次询问模式，只有在 AI 确实需要读取个人学习资料时才会弹出系统提示。")

    with tab5:
        st.warning("如需退出账号，请使用右上角的“退出空间”。")
