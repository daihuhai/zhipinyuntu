"""
认证路由
- POST /auth/register         注册
- POST /auth/login            登录
- POST /auth/refresh          刷新令牌
- POST /auth/logout           退出 (无状态 JWT, 前端清除即可)
- GET  /auth/me               获取当前用户信息
- PUT  /auth/profile          修改个人信息
- PUT  /auth/change-password  修改密码 (已登录)
- POST /auth/forgot-password  忘记密码重置 (用户名+手机号验证)
"""
from fastapi import APIRouter, Depends, Request, UploadFile, File
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.security import verify_password, hash_password
from app.core.config import settings
from app.db.base import get_db
from app.core.limiter import limiter
from app.models.user import SysUser
from app.schemas.auth import (
    LoginRequest, RefreshTokenRequest, RegisterRequest, TokenResponse, UserInfo,
    ChangePasswordRequest, ForgotPasswordRequest,
)
from app.schemas.common import success, fail, BizError
from app.services import auth_service
from app.services.auth_service import AuthException

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", summary="用户注册", response_model=None)
@limiter.limit("3/minute")
async def register(request: Request, req: RegisterRequest, db: Session = Depends(get_db)):
    """注册个人或企业用户 (速率限制: 3次/分钟/IP)"""
    try:
        data = auth_service.register(req, db)
        return success(data=data, message="注册成功")
    except AuthException as e:
        return fail(e.code, e.message)
    except Exception as e:
        return fail(BizError.SYSTEM_ERROR, f"注册失败: {e}")


@router.post("/login", summary="用户登录", response_model=None)
@limiter.limit("5/minute")
async def login(request: Request, req: LoginRequest, db: Session = Depends(get_db)):
    """用户名 / 手机号 / 邮箱 登录 (速率限制: 5次/分钟/IP)"""
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
        "id_card": current_user.id_card,
        "birth_date": current_user.birth_date.isoformat() if current_user.birth_date else None,
        "education": current_user.education,
        "work_years": current_user.work_years,
        "status": current_user.status,
        "is_vip": current_user.vip_active,
        "vip_expire_at": current_user.vip_expire_at.isoformat() if current_user.vip_expire_at else None,
        "onboard_done": current_user.onboard_done,
    }
    return success(data=data)


@router.post("/onboard-done", summary="标记新用户引导完成", response_model=None)
async def onboard_done(
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """标记当前用户已完成新用户引导, 之后登录不再展示引导"""
    if current_user.onboard_done != 1:
        current_user.onboard_done = 1
        db.commit()
    return success(message="引导完成状态已保存")


@router.put("/profile", summary="修改个人信息", response_model=None)
async def update_profile(
    payload: dict,
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """修改当前用户个人信息 (昵称/手机/邮箱/企业名称等)"""
    try:
        # 可编辑字段白名单
        allowed_fields = {
            "nickname", "phone", "email", "avatar_url",
            "company_name", "contact_person", "real_name", "gender",
            "id_card", "education", "work_years",
        }
        updated = []
        for field in allowed_fields:
            if field in payload:
                val = payload[field]
                if val is not None:
                    setattr(current_user, field, val)
                    updated.append(field)
        if not updated:
            return fail(BizError.VALIDATION_ERROR, "没有可更新的字段")
        db.commit()
        db.refresh(current_user)
        data = {
            "user_id": current_user.id,
            "username": current_user.username,
            "nickname": current_user.nickname,
            "role": current_user.role,
            "avatar_url": current_user.avatar_url,
            "phone": current_user.phone,
            "email": current_user.email,
            "company_name": current_user.company_name,
            "contact_person": current_user.contact_person,
            "real_name": current_user.real_name,
            "gender": current_user.gender,
            "id_card": current_user.id_card,
            "education": current_user.education,
            "work_years": current_user.work_years,
        }
        return success(data=data, message="个人信息更新成功")
    except Exception as e:
        db.rollback()
        return fail(BizError.SYSTEM_ERROR, f"更新失败: {e}")


@router.put("/change-password", summary="修改密码", response_model=None)
@limiter.limit("5/minute")
async def change_password(
    request: Request,
    req: ChangePasswordRequest,
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """修改密码 (需登录, 验证原密码后更新)"""
    # 验证原密码
    if not verify_password(req.old_password, current_user.password_hash):
        return fail(BizError.VALIDATION_ERROR, "原密码不正确")
    # 新密码不能与原密码相同
    if req.old_password == req.new_password:
        return fail(BizError.VALIDATION_ERROR, "新密码不能与原密码相同")
    try:
        current_user.password_hash = hash_password(req.new_password)
        db.commit()
        return success(message="密码修改成功, 请重新登录")
    except Exception as e:
        db.rollback()
        return fail(BizError.SYSTEM_ERROR, f"密码修改失败: {e}")


@router.post("/forgot-password", summary="忘记密码重置", response_model=None)
@limiter.limit("3/minute")
async def forgot_password(
    request: Request,
    req: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    """忘记密码重置 (通过用户名+手机号验证身份后重置密码)"""
    user = db.execute(
        select(SysUser).where(
            SysUser.username == req.username,
            SysUser.phone == req.phone,
        )
    ).scalar_one_or_none()

    if user is None:
        # 不透露用户是否存在, 统一返回模糊提示
        return fail(BizError.VALIDATION_ERROR, "用户名与手机号不匹配")
    if user.status != 1:
        return fail(BizError.ROLE_FORBIDDEN, "账号已被禁用, 联系管理员")

    try:
        user.password_hash = hash_password(req.new_password)
        db.commit()
        return success(message="密码重置成功, 请使用新密码登录")
    except Exception as e:
        db.rollback()
        return fail(BizError.SYSTEM_ERROR, f"密码重置失败: {e}")


# 允许的头像图片类型
AVATAR_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
AVATAR_MAX_SIZE = 2 * 1024 * 1024  # 2MB


@router.post("/avatar", summary="上传头像", response_model=None)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """上传头像图片, 保存到 /uploads/avatars/ 目录, 更新用户 avatar_url"""
    import os, hashlib
    from datetime import datetime
    from pathlib import Path

    # 校验文件类型
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in AVATAR_EXTENSIONS:
        return fail(BizError.VALIDATION_ERROR, f"不支持的图片类型: {ext}, 仅支持 {', '.join(AVATAR_EXTENSIONS)}")

    # 读取文件内容
    content = await file.read()
    if len(content) > AVATAR_MAX_SIZE:
        return fail(BizError.VALIDATION_ERROR, f"图片过大, 上限 {AVATAR_MAX_SIZE // 1024 // 1024}MB")

    # 保存文件
    storage_path = Path(settings.STORAGE_PATH).resolve()
    save_dir = storage_path / "avatars"
    save_dir.mkdir(parents=True, exist_ok=True)

    file_hash = hashlib.md5(content).hexdigest()
    now = datetime.now()
    filename = f"{now.strftime('%Y%m%d%H%M%S')}_{file_hash[:8]}{ext}"
    file_path = save_dir / filename
    file_path.write_bytes(content)

    # 相对访问 URL
    rel_path = file_path.relative_to(storage_path).as_posix()
    avatar_url = f"/uploads/{rel_path}"

    # 更新用户头像
    current_user.avatar_url = avatar_url
    db.commit()

    return success(data={"avatar_url": avatar_url}, message="头像上传成功")
