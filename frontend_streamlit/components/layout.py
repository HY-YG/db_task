from __future__ import annotations

import streamlit as st

from frontend_streamlit.config import APP_TITLE, PAGE_ICONS, PAGE_LABELS
from frontend_streamlit.pages.account_page import render_account_dialog
from frontend_streamlit.state import set_page


def inject_global_styles() -> None:
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"], [data-testid="collapsedControl"], #MainMenu, footer, header {
            display: none !important;
        }
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 2rem !important;
            max-width: 95% !important;
        }
        /* Custom scrollbar for better appearance */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        ::-webkit-scrollbar-track {
            background: transparent;
        }
        ::-webkit-scrollbar-thumb {
            background: #cbd0e1;
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #a9b0cc;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_topbar(user_info: dict) -> None:
    col1, col2, col3 = st.columns([2, 5, 2], vertical_alignment="center")
    with col1:
        st.markdown(f"<h3 style='margin:0; color: #5a67df;'>{APP_TITLE}</h3>", unsafe_allow_html=True)
    with col3:
        user_name = user_info.get("name") or "Teacher Zhang"
        with st.popover(f"👤 {user_name} ▾", use_container_width=True):
            if st.button("⚙️ 账号管理", use_container_width=True):
                render_account_dialog(user_info)
            if st.button("🔄 切换角色", use_container_width=True):
                st.toast("演示版：暂不支持切换角色")
            if st.button("🚪 退出空间", use_container_width=True):
                st.toast("演示版：暂不支持退出")


def render_side_navigation(user_info: dict) -> None:
    st.markdown(
        f"""
        <div style="background: linear-gradient(135deg, #5a67df 0%, #4654c9 100%); 
                    border-radius: 16px; padding: 24px 16px; color: white; text-align: center;
                    margin-bottom: 1.5rem; box-shadow: 0 10px 20px rgba(90,103,223,0.15);">
            <div style="width: 64px; height: 64px; background: #ffca28; border-radius: 50%; 
                        margin: 0 auto 12px; display: flex; align-items: center; justify-content: center;
                        font-size: 24px; font-weight: bold; color: white;
                        box-shadow: 0 4px 10px rgba(255,202,40,0.3);">
                {str(user_info.get("name", "T"))[:2]}
            </div>
            <div style="font-weight: bold; font-size: 1.1rem; letter-spacing: 0.5px;">{user_info.get("name")}</div>
            <div style="font-size: 0.85rem; opacity: 0.85; margin-top: 4px;">学生空间</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    for key in ("courses", "inbox", "notes_plans", "assignments", "ai_assistant"):
        label = f"{PAGE_ICONS[key]} {PAGE_LABELS[key]}"
        st.button(
            label,
            key=f"nav-{key}",
            use_container_width=True,
            type="primary" if st.session_state.current_page == key else "secondary",
            on_click=set_page,
            args=(key,),
        )
