"""
平台管理后台路由 (M5) - 仅 ROLE_ADMIN 可访问
- 仪表盘: GET /admin/dashboard
- 用户管理: GET/PUT/DELETE /admin/users
- 简历管理: GET/DELETE /admin/resumes
- 职位管理: GET/PUT/DELETE /admin/jobs
- 操作日志: GET /admin/logs
"""
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.deps import require_role
from app.db.base import get_db
from app.models.user import SysUser
from app.schemas.common import success, fail, BizError
from app.services.admin_service import admin_service

router = APIRouter(prefix="/admin", tags=["平台管理"], dependencies=[Depends(require_role("ROLE_ADMIN"))])


# ===== 仪表盘 =====
@router.get("/dashboard", summary="管理后台仪表盘")
async def dashboard(
    current_user: SysUser = Depends(require_role("ROLE_ADMIN")),
    db: Session = Depends(get_db),
):
    """获取仪表盘统计数据 (用户/简历/职位/匹配)"""
    data = admin_service.get_dashboard_stats(db)
    return success(data=data)


# ===== 用户管理 =====
@router.get("/users", summary="用户列表")
async def list_users(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    role: str | None = Query(None),
    status: int | None = Query(None),
    keyword: str = Query(""),
    db: Session = Depends(get_db),
):
    data = admin_service.list_users(db, page, size, role, status, keyword)
    return success(data=data)


@router.get("/users/{user_id}", summary="用户详情")
async def get_user(user_id: int, db: Session = Depends(get_db)):
    try:
        data = admin_service.get_user(user_id, db)
        return success(data=data)
    except ValueError as e:
        return fail(BizError.NOT_FOUND, str(e))


@router.put("/users/{user_id}/status", summary="启用/禁用用户")
async def update_user_status(
    user_id: int,
    payload: dict,
    current_user: SysUser = Depends(require_role("ROLE_ADMIN")),
    db: Session = Depends(get_db),
    request: Request = None,
):
    try:
        new_status = int(payload.get("status", 1))
        admin_service.update_user_status(user_id, new_status, db)
        admin_service.write_log(
            db, current_user.id, "UPDATE_USER_STATUS",
            target_type="user", target_id=user_id,
            detail=f"状态修改为 {new_status}",
            ip=request.client.host if request else None,
        )
        return success(message="状态已更新")
    except ValueError as e:
        return fail(BizError.BAD_REQUEST, str(e))


@router.put("/users/{user_id}/role", summary="修改用户角色")
async def update_user_role(
    user_id: int,
    payload: dict,
    current_user: SysUser = Depends(require_role("ROLE_ADMIN")),
    db: Session = Depends(get_db),
    request: Request = None,
):
    try:
        new_role = payload.get("role", "")
        admin_service.update_user_role(user_id, new_role, db)
        admin_service.write_log(
            db, current_user.id, "UPDATE_USER_ROLE",
            target_type="user", target_id=user_id,
            detail=f"角色修改为 {new_role}",
            ip=request.client.host if request else None,
        )
        return success(message="角色已更新")
    except ValueError as e:
        return fail(BizError.BAD_REQUEST, str(e))


@router.delete("/users/{user_id}", summary="删除用户")
async def delete_user(
    user_id: int,
    current_user: SysUser = Depends(require_role("ROLE_ADMIN")),
    db: Session = Depends(get_db),
    request: Request = None,
):
    try:
        admin_service.delete_user(user_id, db)
        admin_service.write_log(
            db, current_user.id, "DELETE_USER",
            target_type="user", target_id=user_id,
            ip=request.client.host if request else None,
        )
        return success(message="已删除")
    except ValueError as e:
        return fail(BizError.BAD_REQUEST, str(e))


# ===== 简历管理 =====
@router.get("/resumes", summary="简历列表")
async def list_resumes(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    keyword: str = Query(""),
    parse_status: int | None = Query(None),
    db: Session = Depends(get_db),
):
    data = admin_service.list_resumes(db, page, size, keyword, parse_status)
    return success(data=data)


@router.delete("/resumes/{resume_id}", summary="删除简历")
async def delete_resume(
    resume_id: int,
    current_user: SysUser = Depends(require_role("ROLE_ADMIN")),
    db: Session = Depends(get_db),
    request: Request = None,
):
    try:
        admin_service.delete_resume(resume_id, db)
        admin_service.write_log(
            db, current_user.id, "DELETE_RESUME",
            target_type="resume", target_id=resume_id,
            ip=request.client.host if request else None,
        )
        return success(message="已删除")
    except ValueError as e:
        return fail(BizError.BAD_REQUEST, str(e))


# ===== 职位管理 =====
@router.get("/jobs", summary="职位列表")
async def list_jobs(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    keyword: str = Query(""),
    status: int | None = Query(None),
    db: Session = Depends(get_db),
):
    data = admin_service.list_jobs(db, page, size, keyword, status)
    return success(data=data)


@router.put("/jobs/{job_id}/status", summary="审核/上下架职位")
async def update_job_status(
    job_id: int,
    payload: dict,
    current_user: SysUser = Depends(require_role("ROLE_ADMIN")),
    db: Session = Depends(get_db),
    request: Request = None,
):
    try:
        new_status = int(payload.get("status", 1))
        admin_service.update_job_status(job_id, new_status, db)
        admin_service.write_log(
            db, current_user.id, "UPDATE_JOB_STATUS",
            target_type="job", target_id=job_id,
            detail=f"状态修改为 {new_status}",
            ip=request.client.host if request else None,
        )
        return success(message="状态已更新")
    except ValueError as e:
        return fail(BizError.BAD_REQUEST, str(e))


@router.delete("/jobs/{job_id}", summary="删除职位")
async def delete_job(
    job_id: int,
    current_user: SysUser = Depends(require_role("ROLE_ADMIN")),
    db: Session = Depends(get_db),
    request: Request = None,
):
    try:
        admin_service.delete_job(job_id, db)
        admin_service.write_log(
            db, current_user.id, "DELETE_JOB",
            target_type="job", target_id=job_id,
            ip=request.client.host if request else None,
        )
        return success(message="已删除")
    except ValueError as e:
        return fail(BizError.BAD_REQUEST, str(e))


# ===== 操作日志 =====
@router.get("/logs", summary="操作日志")
async def list_logs(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    admin_id: int | None = Query(None),
    action: str | None = Query(None),
    db: Session = Depends(get_db),
):
    data = admin_service.list_logs(db, page, size, admin_id, action)
    return success(data=data)
