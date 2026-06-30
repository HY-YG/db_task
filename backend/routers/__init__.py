"""routers 子包初始化文件，用于组织相关模块的导入边界。"""

from backend.routers import (
    admin,
    ai,
    auth,
    assignments,
    courses,
    learning,
    users,
)

__all__ = [
    "admin",
    "ai",
    "auth",
    "assignments",
    "courses",
    "learning",
    "users",
]
