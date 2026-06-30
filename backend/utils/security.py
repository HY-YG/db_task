"""封装密码哈希、Token 生成校验等安全相关能力。"""

import hashlib
import hmac
import os


def get_password_hash(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return f"{salt.hex()}${digest.hex()}"


def verify_password(plain_password: str, hashed_password: str | None) -> bool:
    if not hashed_password or "$" not in hashed_password:
        return False
    salt_hex, digest_hex = hashed_password.split("$", 1)
    salt = bytes.fromhex(salt_hex)
    expected = bytes.fromhex(digest_hex)
    actual = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, 100_000)
    return hmac.compare_digest(actual, expected)
