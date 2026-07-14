"""
认证相关 Pydantic Schema
- 注册 / 登录请求
- 令牌响应
- 用户信息
"""
import re
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


# ===== 角色 =====
Role = Literal["ROLE_SEEKER", "ROLE_EMPLOYER", "ROLE_ADMIN"]
Gender = Literal["男", "女", ""]


# ===== 请求 Schema =====
class RegisterRequest(BaseModel):
    """注册请求 (个人或企业)"""
    username: str = Field(..., min_length=3, max_length=64, description="用户名")
    password: str = Field(..., min_length=8, max_length=64, description="密码 (至少8位, 含字母+数字)")
    role: Role = Field(..., description="注册角色: ROLE_SEEKER / ROLE_EMPLOYER")
    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$", description="手机号")
    email: Optional[str] = None

    # 个人用户字段
    nickname: Optional[str] = None
    real_name: Optional[str] = None
    gender: Optional[str] = None
    id_card: Optional[str] = Field(None, max_length=18, description="身份证号")
    education: Optional[str] = Field(None, max_length=32, description="最高学历")
    work_years: Optional[int] = Field(None, ge=0, le=50, description="工作年限")

    # 企业用户字段
    company_name: Optional[str] = None
    credit_code: Optional[str] = None
    contact_person: Optional[str] = None

    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        """密码复杂度: 至少 8 位, 必须同时包含字母和数字"""
        if not re.search(r"[A-Za-z]", v):
            raise ValueError("密码必须包含至少一个字母")
        if not re.search(r"\d", v):
            raise ValueError("密码必须包含至少一个数字")
        return v

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
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    """修改密码请求 (已登录用户)"""
    old_password: str = Field(..., min_length=1, description="原密码")
    new_password: str = Field(..., min_length=8, max_length=64, description="新密码 (至少8位, 含字母+数字)")

    @field_validator("new_password")
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        """密码复杂度: 至少 8 位, 必须同时包含字母和数字"""
        if not re.search(r"[A-Za-z]", v):
            raise ValueError("密码必须包含至少一个字母")
        if not re.search(r"\d", v):
            raise ValueError("密码必须包含至少一个数字")
        return v


class ForgotPasswordRequest(BaseModel):
    """忘记密码重置请求 (通过用户名+手机号验证)"""
    username: str = Field(..., min_length=3, max_length=64, description="用户名")
    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$", description="注册时填写的手机号")
    new_password: str = Field(..., min_length=8, max_length=64, description="新密码 (至少8位, 含字母+数字)")

    @field_validator("new_password")
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        """密码复杂度: 至少 8 位, 必须同时包含字母和数字"""
        if not re.search(r"[A-Za-z]", v):
            raise ValueError("密码必须包含至少一个字母")
        if not re.search(r"\d", v):
            raise ValueError("密码必须包含至少一个数字")
        return v


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
