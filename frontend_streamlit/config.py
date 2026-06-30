"""定义前端运行配置、接口地址与页面级常量。"""

from __future__ import annotations

import os

APP_TITLE = "智学空间"
DEFAULT_BASE_URL = os.getenv("STREAMLIT_BACKEND_URL", "http://127.0.0.1:8000")

PAGE_LABELS = {
    "courses": "课程",
    "progress_dashboard": "进度看板",
    "course_management": "课程管理",
    "user_management": "用户管理",
    "inbox": "收件箱",
    "notes_plans": "笔记/学习计划",
    "assignments": "作业",
    "ai_assistant": "AI助手",
    "account": "账号管理",
}

PAGE_ICONS = {
    "courses": "📚",
    "progress_dashboard": "📈",
    "course_management": "🛠️",
    "user_management": "👥",
    "inbox": "✉️",
    "notes_plans": "📝",
    "assignments": "📋",
    "ai_assistant": "🤖",
    "account": "👤",
}

ACCOUNT_TABS = {
    "basic": "基本资料",
    "avatar": "修改头像",
    "password": "密码管理",
    "danger": "注销账号",
}
