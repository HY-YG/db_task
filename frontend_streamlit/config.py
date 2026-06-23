from __future__ import annotations

import os

APP_TITLE = "智学空间"
DEFAULT_BASE_URL = os.getenv("STREAMLIT_BACKEND_URL", "http://127.0.0.1:8000")
DEFAULT_USER_ID = int(os.getenv("STREAMLIT_USER_ID", "1"))

PAGE_LABELS = {
    "courses": "课程",
    "inbox": "收件箱",
    "notes_plans": "笔记/学习计划",
    "assignments": "作业",
    "ai_assistant": "AI助手",
    "account": "账号管理",
}

PAGE_ICONS = {
    "courses": "📚",
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

