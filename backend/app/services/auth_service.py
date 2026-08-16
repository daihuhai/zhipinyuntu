"""
认证业务服务
- 注册 (个人/企业)
- 登录 (用户名/手机号/邮箱)
- 刷新令牌
- 退出登录
"""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token, create_refresh_token, decode_token, hash_password, verify_password,
)
from app.models.user import SysUser
from app.schemas.auth import RegisterRequest, UserInfo
from app.schemas.common import BizError


class AuthException(Exception):
    """认证业务异常"""

    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


def register(req: RegisterRequest, db: Session) -> dict:
    """用户注册"""
    # 唯一性校验: username / phone
    stmt = select(SysUser).where(
        or_(SysUser.username == req.username, SysUser.phone == req.phone)
    )
    existing = db.execute(stmt).scalars().first()
    if existing:
        if existing.username == req.username:
            raise AuthException(BizError.USER_EXISTS, "用户名已存在")
        raise AuthException(BizError.USER_EXISTS, "手机号已注册")

    # email 唯一性 (若提供)
    if req.email:
        if db.execute(select(SysUser).where(SysUser.email == req.email)).scalars().first():
            raise AuthException(BizError.USER_EXISTS, "邮箱已注册")

    # 企业用户必填校验
    if req.role == "ROLE_EMPLOYER":
        if not req.company_name or not req.credit_code:
            raise AuthException(BizError.VALIDATION_ERROR, "企业用户需填写公司名称与统一社会信用代码")

    # 创建用户
    user = SysUser(
        username=req.username,
        password_hash=hash_password(req.password),
        role=req.role,
        phone=req.phone,
        email=req.email,
        nickname=req.nickname or (req.company_name if req.role == "ROLE_EMPLOYER" else req.username),
        # 企业字段
        company_name=req.company_name,
        credit_code=req.credit_code,
        contact_person=req.contact_person,
        # 个人字段
        real_name=req.real_name,
        gender=req.gender,
        id_card=req.id_card,
        education=req.education,
        work_years=req.work_years,
        status=1,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return _build_token_pair(user)


def login(account: str, password: str, db: Session) -> dict:
    """登录 (支持 用户名 / 手机号 / 邮箱)"""
    stmt = select(SysUser).where(
        or_(
            SysUser.username == account,
            SysUser.phone == account,
            SysUser.email == account,
        )
    )
    user = db.execute(stmt).scalars().first()

    if user is None:
        raise AuthException(BizError.USER_NOT_FOUND, "账号不存在")

    if not verify_password(password, user.password_hash):
        raise AuthException(BizError.PASSWORD_ERROR, "密码错误")

    if user.status != 1:
        raise AuthException(BizError.USER_DISABLED, "账号已被禁用")

    # 更新最后登录时间
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)

    return _build_token_pair(user)


def refresh_access_token(refresh_token: str, db: Session) -> dict:
    """用 refresh token 换取新的 access token"""
    payload = decode_token(refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise AuthException(BizError.TOKEN_INVALID, "刷新令牌无效或已过期")

    user_id = payload.get("sub")
    if not user_id:
        raise AuthException(BizError.TOKEN_INVALID, "令牌载荷缺失")

    user = db.get(SysUser, int(user_id))
    if user is None or user.status != 1:
        raise AuthException(BizError.USER_DISABLED, "用户不存在或已被禁用")

    # 签发新令牌对
    return _build_token_pair(user)


def get_user_info(user: SysUser) -> UserInfo:
    """获取当前用户信息"""
    return UserInfo.model_validate(user)


def _build_token_pair(user: SysUser) -> dict:
    """构造令牌响应"""
    access_token = create_access_token(user.id, user.role)
    refresh_token = create_refresh_token(user.id)
    expires_in = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    return {
        "user_id": user.id,
        "username": user.username,
        "nickname": user.nickname,
        "role": user.role,
        "avatar_url": user.avatar_url,
        "onboard_done": user.onboard_done,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_in": expires_in,
        "token_type": "Bearer",
    }
