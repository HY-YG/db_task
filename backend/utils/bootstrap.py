"""负责系统初始化时的数据库结构补齐、默认角色与管理员账号准备。"""

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.roles_mod import Role
from backend.models.users_mod import User
from backend.utils.security import get_password_hash


async def ensure_auth_schema(db: AsyncSession) -> None:
    await db.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS username VARCHAR(50)"))
    await db.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255)"))
    await db.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE"))
    await db.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW()"))
    await db.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_username ON users (username)"))
    await db.commit()


async def ensure_learning_schema(db: AsyncSession) -> None:
    await db.execute(text("ALTER TABLE assignment_submissions ADD COLUMN IF NOT EXISTS teacher_feedback TEXT"))
    await db.execute(text("ALTER TABLE assignment_submissions ADD COLUMN IF NOT EXISTS score INTEGER"))
    await db.execute(text("ALTER TABLE assignment_submissions ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMPTZ"))
    await db.commit()


async def ensure_default_roles(db: AsyncSession) -> None:
    roles = [
        (1, "学生", "学生可选课、学习、提交作业并跟踪进度"),
        (2, "教师", "教师可维护授课课程、发布作业和通知"),
        (3, "管理员", "管理员可管理用户、课程、作业和通知"),
    ]
    for role_id, role_name, permission_description in roles:
        role = await db.get(Role, role_id)
        if role is None:
            db.add(Role(role_id=role_id, role_name=role_name, permission_description=permission_description))
        else:
            role.role_name = role_name
            role.permission_description = permission_description
    await db.commit()


async def ensure_default_admin_account(db: AsyncSession) -> None:
    result = await db.execute(select(User).where(User.role_id == 3).order_by(User.user_id))
    admin_user = result.scalars().first()
    default_hash = get_password_hash("admin123456")
    if admin_user is None:
        admin_user = User(
            name="系统管理员",
            username="admin",
            password_hash=default_hash,
            role_id=3,
            gender="未设置",
            age=None,
            is_active=True,
        )
        db.add(admin_user)
        await db.commit()
        return

    changed = False
    if not admin_user.username:
        admin_user.username = "admin"
        changed = True
    if not admin_user.password_hash:
        admin_user.password_hash = default_hash
        changed = True
    if not admin_user.is_active:
        admin_user.is_active = True
        changed = True
    if changed:
        db.add(admin_user)
        await db.commit()
