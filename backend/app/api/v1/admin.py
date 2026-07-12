"""
平台管理后台路由 (M5) - 仅 ROLE_ADMIN 可访问
- 仪表盘: GET /admin/dashboard
- 用户管理: GET/PUT/DELETE /admin/users
- 简历管理: GET/DELETE /admin/resumes
- 职位管理: GET/PUT/DELETE /admin/jobs
- 操作日志: GET /admin/logs
- 数据导出: GET /admin/export/{module}
"""
import csv
import io
from datetime import datetime

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import require_role
from app.db.base import get_db
from app.models.user import SysUser
from app.models.resume import Resume
from app.models.job import Job
from app.schemas.common import success, fail, BizError
from app.services.admin_service import admin_service

router = APIRouter(prefix="/admin", tags=["平台管理"], dependencies=[Depends(require_role("ROLE_ADMIN"))])


# 角色中文映射
_ROLE_TEXT = {"ROLE_SEEKER": "个人", "ROLE_EMPLOYER": "企业", "ROLE_ADMIN": "管理员"}
# 简历解析状态映射
_RESUME_STATUS = {0: "待解析", 1: "解析中", 2: "成功", 3: "失败"}
# 职位状态映射
_JOB_STATUS = {0: "下架", 1: "招聘中", 2: "草稿"}


# ===== 仪表盘 =====
@router.get("/dashboard", summary="管理后台仪表盘")
async def dashboard(
    current_user: SysUser = Depends(require_role("ROLE_ADMIN")),
    db: Session = Depends(get_db),
):
    """获取仪表盘统计数据 (用户/简历/职位/匹配)"""
    data = admin_service.get_dashboard_stats(db)
    return success(data=data)


@router.get("/dashboard/trend", summary="仪表盘趋势数据 (图表)")
async def dashboard_trend(
    current_user: SysUser = Depends(require_role("ROLE_ADMIN")),
    db: Session = Depends(get_db),
):
    """获取仪表盘图表数据: 用户增长趋势 + 简历状态分布 + 职位状态分布 + 热门技能 Top10"""
    data = admin_service.get_dashboard_trend(db)
    return success(data=data)


# ===== 大数据中心扩展接口 =====
@router.get("/dashboard/overview", summary="大数据中心总览 (KPI+Gauge)")
async def dashboard_overview(
    current_user: SysUser = Depends(require_role("ROLE_ADMIN")),
    db: Session = Depends(get_db),
):
    """聚合返回 6 个 KPI + 环比数据 + 3 个 Gauge 指标"""
    data = admin_service.get_dashboard_overview(db)
    return success(data=data)


@router.get("/dashboard/applications", summary="投递统计")
async def dashboard_applications(
    current_user: SysUser = Depends(require_role("ROLE_ADMIN")),
    db: Session = Depends(get_db),
):
    """投递总数 + 状态分布"""
    data = admin_service.get_application_stats(db)
    return success(data=data)


@router.get("/dashboard/match-dist", summary="匹配分直方图")
async def dashboard_match_dist(
    current_user: SysUser = Depends(require_role("ROLE_ADMIN")),
    db: Session = Depends(get_db),
):
    """匹配分分桶统计 (0-20/20-40/40-60/60-80/80-100)"""
    data = admin_service.get_match_distribution(db)
    return success(data=data)


@router.get("/dashboard/city-dist", summary="职位城市分布 TOP10")
async def dashboard_city_dist(
    current_user: SysUser = Depends(require_role("ROLE_ADMIN")),
    db: Session = Depends(get_db),
):
    """按 work_city 聚合职位数 TOP10"""
    data = admin_service.get_city_distribution(db)
    return success(data=data)


@router.get("/dashboard/school-rank", summary="院校 TOP10")
async def dashboard_school_rank(
    current_user: SysUser = Depends(require_role("ROLE_ADMIN")),
    db: Session = Depends(get_db),
):
    """按 school 聚合简历数 TOP10"""
    data = admin_service.get_school_rank(db)
    return success(data=data)


@router.get("/dashboard/realtime-logs", summary="实时操作日志")
async def dashboard_realtime_logs(
    current_user: SysUser = Depends(require_role("ROLE_ADMIN")),
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
):
    """最近 N 条操作日志 (供滚动流)"""
    data = admin_service.get_realtime_logs(db, limit)
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


@router.post("/users/batch-status", summary="批量更新用户状态")
async def batch_update_user_status(
    payload: dict,
    current_user: SysUser = Depends(require_role("ROLE_ADMIN")),
    db: Session = Depends(get_db),
    request: Request = None,
):
    """批量更新用户状态 (ids 列表 + status, 跳过管理员)"""
    ids = payload.get("ids") or []
    status = payload.get("status")
    if not isinstance(ids, list) or not ids:
        return fail(BizError.VALIDATION_ERROR, "ids 不能为空")
    if status is None:
        return fail(BizError.VALIDATION_ERROR, "status 不能为空")
    try:
        count = admin_service.batch_update_user_status(ids, int(status), db)
        admin_service.write_log(
            db, current_user.id, "BATCH_UPDATE_USER_STATUS",
            target_type="user",
            detail=f"批量更新 {count} 个用户状态为 {status}, ids={ids}",
            ip=request.client.host if request else None,
        )
        return success(data={"updated": count}, message=f"已更新 {count} 条记录")
    except ValueError as e:
        return fail(BizError.VALIDATION_ERROR, str(e))


@router.get("/users/{user_id}", summary="用户详情")
async def get_user(user_id: int, db: Session = Depends(get_db)):
    try:
        data = admin_service.get_user(user_id, db)
        return success(data=data)
    except ValueError as e:
        return fail(BizError.RESOURCE_NOT_FOUND, str(e))


@router.get("/users/{user_id}/detail", summary="用户详情 (含关联统计)")
async def get_user_detail(user_id: int, db: Session = Depends(get_db)):
    """获取用户详情 + 关联统计 (简历数/投递数/职位数/收到投递数)"""
    try:
        data = admin_service.get_user_detail(user_id, db)
        return success(data=data)
    except ValueError as e:
        return fail(BizError.RESOURCE_NOT_FOUND, str(e))


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


@router.post("/resumes/batch-delete", summary="批量删除简历")
async def batch_delete_resumes(
    payload: dict,
    current_user: SysUser = Depends(require_role("ROLE_ADMIN")),
    db: Session = Depends(get_db),
    request: Request = None,
):
    """批量删除简历 (ids 列表)"""
    ids = payload.get("ids") or []
    if not isinstance(ids, list) or not ids:
        return fail(BizError.VALIDATION_ERROR, "ids 不能为空")
    try:
        count = admin_service.batch_delete_resumes(ids, db)
        admin_service.write_log(
            db, current_user.id, "BATCH_DELETE_RESUMES",
            target_type="resume",
            detail=f"批量删除 {count} 条简历, ids={ids}",
            ip=request.client.host if request else None,
        )
        return success(data={"deleted": count}, message=f"已删除 {count} 条记录")
    except ValueError as e:
        return fail(BizError.VALIDATION_ERROR, str(e))


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


@router.post("/jobs/batch-status", summary="批量更新职位状态")
async def batch_update_job_status(
    payload: dict,
    current_user: SysUser = Depends(require_role("ROLE_ADMIN")),
    db: Session = Depends(get_db),
    request: Request = None,
):
    """批量更新职位状态 (ids 列表 + status)"""
    ids = payload.get("ids") or []
    status = payload.get("status")
    if not isinstance(ids, list) or not ids:
        return fail(BizError.VALIDATION_ERROR, "ids 不能为空")
    if status is None:
        return fail(BizError.VALIDATION_ERROR, "status 不能为空")
    try:
        count = admin_service.batch_update_job_status(ids, int(status), db)
        admin_service.write_log(
            db, current_user.id, "BATCH_UPDATE_JOB_STATUS",
            target_type="job",
            detail=f"批量更新 {count} 个职位状态为 {status}, ids={ids}",
            ip=request.client.host if request else None,
        )
        return success(data={"updated": count}, message=f"已更新 {count} 条记录")
    except ValueError as e:
        return fail(BizError.VALIDATION_ERROR, str(e))


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


# ===== 数据导出 (CSV) =====
@router.get("/export/{module}", summary="导出数据 (CSV)")
async def export_data(
    module: str,
    current_user: SysUser = Depends(require_role("ROLE_ADMIN")),
    db: Session = Depends(get_db),
    request: Request = None,
):
    """导出用户/简历/职位数据为 CSV (带 BOM 头避免 Excel 中文乱码)
    module: users | resumes | jobs
    """
    if module not in ("users", "resumes", "jobs"):
        return fail(BizError.VALIDATION_ERROR, "导出模块非法, 仅支持 users / resumes / jobs")

    # 用 StringIO 拼装 CSV, 首部写入 BOM (\ufeff) 解决 Excel 中文乱码
    buf = io.StringIO()
    buf.write("\ufeff")
    writer = csv.writer(buf)

    if module == "users":
        writer.writerow(["ID", "用户名", "角色", "手机", "邮箱", "状态", "注册时间"])
        rows = list(db.execute(
            select(SysUser).order_by(SysUser.created_at.desc())
        ).scalars())
        for u in rows:
            writer.writerow([
                u.id, u.username, _ROLE_TEXT.get(u.role, u.role),
                u.phone or "", u.email or "",
                "启用" if u.status == 1 else "禁用",
                u.created_at.strftime("%Y-%m-%d %H:%M:%S") if u.created_at else "",
            ])
    elif module == "resumes":
        writer.writerow(["ID", "姓名", "学历", "学校", "专业", "工作年限", "城市", "手机", "邮箱", "解析状态", "创建时间"])
        rows = list(db.execute(
            select(Resume).order_by(Resume.created_at.desc())
        ).scalars())
        for r in rows:
            writer.writerow([
                r.id, r.name or "", r.education or "", r.school or "",
                r.major or "", r.work_years if r.work_years is not None else "",
                r.current_city or "", r.phone or "", r.email or "",
                _RESUME_STATUS.get(r.parse_status, str(r.parse_status)),
                r.created_at.strftime("%Y-%m-%d %H:%M:%S") if r.created_at else "",
            ])
    else:  # jobs
        writer.writerow(["ID", "职位名称", "公司", "城市", "薪资", "学历要求", "招聘人数", "状态", "创建时间"])
        rows = list(db.execute(
            select(Job).order_by(Job.created_at.desc())
        ).scalars())
        for j in rows:
            salary = ""
            if j.salary_min is not None and j.salary_max is not None:
                salary = f"{j.salary_min}-{j.salary_max}K"
            elif j.salary_min is not None:
                salary = f"{j.salary_min}K"
            writer.writerow([
                j.id, j.title, j.company or "", j.work_city or "",
                salary, j.education_required or "",
                j.headcount if j.headcount is not None else "",
                _JOB_STATUS.get(j.status, str(j.status)),
                j.created_at.strftime("%Y-%m-%d %H:%M:%S") if j.created_at else "",
            ])

    # 文件名带日期
    filename = f"{module}_{datetime.now().strftime('%Y%m%d')}.csv"
    content = buf.getvalue().encode("utf-8")

    # 记录导出操作日志
    try:
        row_count = len(rows) if 'rows' in dir() else 0
        admin_service.write_log(
            db, current_user.id, "EXPORT_DATA",
            target_type=module,
            detail=f"导出 {module} 数据 {row_count} 条, 文件: {filename}",
            ip=request.client.host if request else None,
        )
    except Exception:
        pass

    def _iter():
        yield content

    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
    }
    return StreamingResponse(_iter(), media_type="text/csv; charset=utf-8", headers=headers)
