"""
认证路由
- POST /auth/register  注册
- POST /auth/login     登录
- POST /auth/refresh   刷新令牌
- POST /auth/logout    退出 (无状态 JWT, 前端清除即可)
- GET  /auth/me        获取当前用户信息
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.base import get_db
from app.models.user import SysUser
from app.schemas.auth import (
    LoginRequest, RefreshTokenRequest, RegisterRequest, TokenResponse, UserInfo,
)
from app.schemas.common import success, fail, BizError
from app.services import auth_service
from app.services.auth_service import AuthException

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", summary="用户注册", response_model=None)
async def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """注册个人或企业用户"""
    try:
        data = auth_service.register(req, db)
        return success(data=data, message="注册成功")
    except AuthException as e:
        return fail(e.code, e.message)
    except Exception as e:
        return fail(BizError.SYSTEM_ERROR, f"注册失败: {e}")


@router.post("/login", summary="用户登录", response_model=None)
async def login(req: LoginRequest, db: Session = Depends(get_db)):
    """用户名 / 手机号 / 邮箱 登录"""
    try:
        data = auth_service.login(req.account, req.password, db)
        return success(data=data, message="登录成功")
    except AuthException as e:
        return fail(e.code, e.message)
    except Exception as e:
        return fail(BizError.SYSTEM_ERROR, f"登录失败: {e}")


@router.post("/refresh", summary="刷新令牌", response_model=None)
async def refresh(req: RefreshTokenRequest, db: Session = Depends(get_db)):
    """用 refresh token 换取新的 access token"""
    try:
        data = auth_service.refresh_access_token(req.refresh_token, db)
        return success(data=data, message="刷新成功")
    except AuthException as e:
        return fail(e.code, e.message)
    except Exception as e:
        return fail(BizError.SYSTEM_ERROR, f"刷新失败: {e}")


@router.post("/logout", summary="退出登录", response_model=None)
async def logout(current_user: SysUser = Depends(get_current_user)):
    """退出登录 (无状态 JWT, 前端清除 token 即可)"""
    return success(message=f"再见, {current_user.nickname or current_user.username}")


@router.get("/me", summary="获取当前用户信息", response_model=None)
async def me(current_user: SysUser = Depends(get_current_user)):
    """获取当前登录用户信息"""
    data = {
        "user_id": current_user.id,
        "username": current_user.username,
        "nickname": current_user.nickname,
        "role": current_user.role,
        "avatar_url": current_user.avatar_url,
        "phone": current_user.phone,
        "email": current_user.email,
        "company_name": current_user.company_name,
        "credit_code": current_user.credit_code,
        "contact_person": current_user.contact_person,
        "real_name": current_user.real_name,
        "gender": current_user.gender,
        "status": current_user.status,
    }
    return success(data=data)
