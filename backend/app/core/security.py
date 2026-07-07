"""
安全工具模块
- 密码哈希 (BCrypt)
- JWT 令牌签发与校验 (python-jose)
"""
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import jwt, JWTError

from app.core.config import settings


# ===== 密码哈希 =====
_BCRYPT_MAX = 72  # bcrypt 限制密码最长 72 字节


def hash_password(password: str) -> str:
    """对明文密码进行 BCrypt 哈希 (UTF-8 编码, 超过 72 字节截断)"""
    pwd_bytes = password.encode("utf-8")[:_BCRYPT_MAX]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    """校验明文密码与哈希是否匹配"""
    try:
        pwd_bytes = plain_password.encode("utf-8")[:_BCRYPT_MAX]
        return bcrypt.checkpw(pwd_bytes, password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


# ===== JWT 令牌 =====
def _create_token(
    subject: str | int,
    token_type: str,
    expires_delta: timedelta,
    extra: dict[str, Any] | None = None,
) -> str:
    """签发 JWT 令牌"""
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_access_token(user_id: int, role: str) -> str:
    """签发 access token (短期, 2h)"""
    return _create_token(
        subject=user_id,
        token_type="access",
        expires_delta=timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
        extra={"role": role},
    )


def create_refresh_token(user_id: int) -> str:
    """签发 refresh token (长期, 7d)"""
    return _create_token(
        subject=user_id,
        token_type="refresh",
        expires_delta=timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
    )


def decode_token(token: str) -> dict[str, Any] | None:
    """解码并校验 JWT 令牌, 失败返回 None"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None
