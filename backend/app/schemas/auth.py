"""
认证相关 Pydantic Schema
- 注册 / 登录请求
- 令牌响应
- 用户信息
"""
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


# ===== 角色 =====
Role = Literal["ROLE_SEEKER", "ROLE_EMPLOYER", "ROLE_ADMIN"]
Gender = Literal["男", "女", ""]


# ===== 请求 Schema =====
class RegisterRequest(BaseModel):
    """注册请求 (个人或企业)"""
    username: str = Field(..., min_length=3, max_length=64, description="用户名")
    password: str = Field(..., min_length=6, max_length=64, description="密码")
    role: Role = Field(..., description="注册角色: ROLE_SEEKER / ROLE_EMPLOYER")
    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$", description="手机号")
    email: Optional[str] = None

    # 个人用户字段
    nickname: Optional[str] = None
    real_name: Optional[str] = None
    gender: Optional[str] = None

    # 企业用户字段
    company_name: Optional[str] = None
    credit_code: Optional[str] = None
    contact_person: Optional[str] = None

    @field_validator("nickname", "real_name", "company_name")
    @classmethod
    def strip_str(cls, v: str | None) -> str | None:
        return v.strip() if v else v


class LoginRequest(BaseModel):
    """登录请求"""
    account: str = Field(..., description="用户名 / 手机号 / 邮箱")
    password: str = Field(..., description="密码")


class RefreshTokenRequest(BaseModel):
    """刷新令牌请求"""
    refresh_token: str = Field(..., description="refresh token")


# ===== 响应 Schema =====
class UserInfo(BaseModel):
    """用户信息 (脱敏)"""
    user_id: int
    username: str
    nickname: Optional[str] = None
    role: str
    avatar_url: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    # 企业
    company_name: Optional[str] = None
    credit_code: Optional[str] = None
    contact_person: Optional[str] = None
    # 个人
    real_name: Optional[str] = None
    gender: Optional[str] = None
    status: int = 1

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """登录/注册成功后的令牌响应"""
    user_id: int
    username: str
    nickname: Optional[str] = None
    role: str
    avatar_url: Optional[str] = None
    access_token: str
    refresh_token: str
    expires_in: int = Field(..., description="access token 有效期(秒)")
    token_type: str = "Bearer"
