"""
投递记录路由
- POST   /applications              投递简历 (求职者)
- GET    /applications              我的投递记录 (求职者)
- GET    /applications/job/{job_id} 某职位的投递记录 (企业)
- POST   /applications/{id}/status  更新投递状态 (企业)
"""
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.core.deps import require_role
from app.db.base import get_db
from app.models.user import SysUser
from app.models.resume import Resume
from app.models.job import Job
from app.models.application import JobApplication
from app.schemas.common import success, fail, BizError

router = APIRouter(prefix="/applications", tags=["投递记录"])


class ApplicationCreateRequest(BaseModel):
    """投递简历请求体"""
    resume_id: int
    job_id: int
    cover_letter: Optional[str] = None


class ApplicationStatusRequest(BaseModel):
    """更新投递状态请求体"""
    status: int


class BatchStatusRequest(BaseModel):
    """批量更新投递状态请求体"""
    ids: list[int]
    status: int


def _application_to_dict(app: JobApplication) -> dict[str, Any]:
    return {
        "id": app.id,
        "resume_id": app.resume_id,
        "job_id": app.job_id,
        "applicant_id": app.applicant_id,
        "status": app.status,
        "cover_letter": app.cover_letter,
        "created_at": app.created_at.isoformat() if app.created_at else None,
    }


@router.post("", summary="投递简历", response_model=None)
async def create_application(
    req: ApplicationCreateRequest,
    current_user: SysUser = Depends(require_role("ROLE_SEEKER")),
    db: Session = Depends(get_db),
):
    """求职者向职位投递简历"""
    # 校验简历归属
    resume = db.get(Resume, req.resume_id)
    if resume is None or resume.user_id != current_user.id:
        return fail(BizError.ROLE_FORBIDDEN, "简历不存在或非本人所有")

    # 校验职位存在且招聘中
    job = db.get(Job, req.job_id)
    if job is None:
        return fail(BizError.RESOURCE_NOT_FOUND, "职位不存在")
    if job.status != 1:
        return fail(BizError.VALIDATION_ERROR, "该职位已下架, 无法投递")

    # 校验是否已投递 (UniqueConstraint)
    exists = db.execute(
        select(JobApplication).where(
            JobApplication.resume_id == req.resume_id,
            JobApplication.job_id == req.job_id,
        )
    ).scalar_one_or_none()
    if exists is not None:
        return fail(BizError.VALIDATION_ERROR, "已投递过该职位, 请勿重复投递")

    try:
        application = JobApplication(
            resume_id=req.resume_id,
            job_id=req.job_id,
            applicant_id=current_user.id,
            status=0,
            cover_letter=req.cover_letter,
        )
        db.add(application)
        db.commit()
        db.refresh(application)
        return success(data=_application_to_dict(application), message="投递成功")
    except Exception as e:
        db.rollback()
        return fail(BizError.SYSTEM_ERROR, f"投递失败: {e}")


@router.get("", summary="我的投递记录", response_model=None)
async def list_my_applications(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: SysUser = Depends(require_role("ROLE_SEEKER")),
    db: Session = Depends(get_db),
):
    """查询当前求职者的投递记录 (含职位信息)"""
    base_stmt = select(JobApplication, Job).join(
        Job, JobApplication.job_id == Job.id
    ).where(JobApplication.applicant_id == current_user.id)

    # 总数
    total = db.execute(
        select(func.count()).select_from(JobApplication).where(
            JobApplication.applicant_id == current_user.id
        )
    ).scalar_one()

    offset = (page - 1) * size
    rows = db.execute(
        base_stmt.order_by(JobApplication.created_at.desc()).offset(offset).limit(size)
    ).all()

    items = [
        {
            **_application_to_dict(app),
            "job": {
                "id": job.id,
                "title": job.title,
                "company": job.company,
                "work_city": job.work_city,
                "salary_min": job.salary_min,
                "salary_max": job.salary_max,
            },
        }
        for app, job in rows
    ]
    return success(data={"items": items, "total": total, "page": page, "size": size})


@router.get("/my/trend", summary="求职者投递趋势 (近14天)", response_model=None)
async def my_application_trend(
    current_user: SysUser = Depends(require_role("ROLE_SEEKER", "ROLE_ADMIN")),
    db: Session = Depends(get_db),
):
    """求职者投递趋势: 近 14 天每日投递量 + 状态分布 + 匹配均分"""
    from datetime import datetime, timedelta

    apps = db.execute(
        select(JobApplication).where(JobApplication.applicant_id == current_user.id)
    ).scalars().all()

    today = datetime.utcnow().date()
    days = [(today - timedelta(days=i)) for i in range(13, -1, -1)]
    day_labels = [d.strftime("%m-%d") for d in days]
    daily_counts = {d: 0 for d in day_labels}

    by_status = {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0}
    for app in apps:
        by_status[str(app.status)] = by_status.get(str(app.status), 0) + 1
        if app.created_at:
            label = app.created_at.strftime("%m-%d")
            if label in daily_counts:
                daily_counts[label] += 1

    return success(data={
        "days": day_labels,
        "counts": [daily_counts[d] for d in day_labels],
        "total": len(apps),
        "by_status": by_status,
    })


@router.get("/job/{job_id}", summary="某职位的投递记录", response_model=None)
async def list_applications_by_job(
    job_id: int,
    current_user: SysUser = Depends(require_role("ROLE_EMPLOYER", "ROLE_ADMIN")),
    db: Session = Depends(get_db),
):
    """查询某职位的投递记录 (含完整简历信息 + 匹配分析)"""
    from sqlalchemy.orm import selectinload

    # 校验职位存在
    job = db.get(Job, job_id)
    if job is None:
        return fail(BizError.RESOURCE_NOT_FOUND, "职位不存在")

    # 预加载简历 + 技能, 避免 N+1 查询
    rows = db.execute(
        select(JobApplication, Resume)
        .join(Resume, JobApplication.resume_id == Resume.id)
        .options(selectinload(Resume.skills))
        .where(JobApplication.job_id == job_id)
        .order_by(JobApplication.created_at.desc())
    ).all()

    # 获取职位技能要求
    req_skills = [r.skill_name for r in job.requirements] if job.requirements else []

    items = []
    for app, resume in rows:
        # 简历技能列表
        resume_skills = [s.skill_name for s in resume.skills] if resume.skills else []
        # 匹配分析
        matched = [s for s in req_skills if s in resume_skills]
        missing = [s for s in req_skills if s not in resume_skills]
        match_score = round(len(matched) / len(req_skills) * 100) if req_skills else 0

        items.append({
            **_application_to_dict(app),
            "resume": {
                "id": resume.id,
                "name": resume.name,
                "gender": resume.gender,
                "age": resume.age,
                "phone": resume.phone,
                "email": resume.email,
                "education": resume.education,
                "school": resume.school,
                "major": resume.major,
                "work_years": resume.work_years,
                "current_city": resume.current_city,
                "self_evaluation": resume.self_evaluation,
                "skills": [{"skill_name": s.skill_name, "skill_level": s.skill_level} for s in resume.skills] if resume.skills else [],
            },
            "match_analysis": {
                "matched": matched,
                "missing": missing,
                "match_score": match_score,
                "total_required": len(req_skills),
            },
        })
    return success(data={"items": items, "total": len(items)})


@router.post("/batch/status", summary="批量更新投递状态", response_model=None)
async def batch_update_status(
    req: BatchStatusRequest,
    current_user: SysUser = Depends(require_role("ROLE_EMPLOYER", "ROLE_ADMIN")),
    db: Session = Depends(get_db),
):
    """企业批量更新投递状态 (0=已投递 1=已查看 2=面试邀请 3=不合适 4=已录用)"""
    if req.status < 0 or req.status > 4:
        return fail(BizError.VALIDATION_ERROR, "状态值非法 (应为 0-4)")
    if not req.ids:
        return fail(BizError.VALIDATION_ERROR, "ids 不能为空")
    try:
        updated = 0
        for app_id in req.ids:
            app = db.get(JobApplication, app_id)
            if app is not None:
                app.status = req.status
                updated += 1
        db.commit()
        return success(data={"updated": updated}, message=f"已更新 {updated} 条记录")
    except Exception as e:
        db.rollback()
        return fail(BizError.SYSTEM_ERROR, f"批量更新失败: {e}")


@router.post("/{application_id}/status", summary="更新投递状态", response_model=None)
async def update_application_status(
    application_id: int,
    req: ApplicationStatusRequest,
    current_user: SysUser = Depends(require_role("ROLE_EMPLOYER", "ROLE_ADMIN")),
    db: Session = Depends(get_db),
):
    """企业更新投递状态 (0=已投递 1=已查看 2=面试邀请 3=不合适 4=已录用)"""
    if req.status < 0 or req.status > 4:
        return fail(BizError.VALIDATION_ERROR, "状态值非法 (应为 0-4)")

    application = db.get(JobApplication, application_id)
    if application is None:
        return fail(BizError.RESOURCE_NOT_FOUND, "投递记录不存在")

    try:
        application.status = req.status
        db.commit()
        db.refresh(application)
        return success(
            data={"id": application.id, "status": application.status},
            message="状态更新成功",
        )
    except Exception as e:
        db.rollback()
        return fail(BizError.SYSTEM_ERROR, f"状态更新失败: {e}")


@router.get("/employer/summary", summary="企业投递统计", response_model=None)
async def employer_application_summary(
    current_user: SysUser = Depends(require_role("ROLE_EMPLOYER", "ROLE_ADMIN")),
    db: Session = Depends(get_db),
):
    """企业总览: 在招职位数, 收到简历数, 各状态分布"""
    # 当前企业的所有职位
    jobs = db.execute(
        select(Job).where(Job.user_id == current_user.id)
    ).scalars().all()
    active_job_count = sum(1 for j in jobs if j.status == 1)
    job_ids = [j.id for j in jobs]

    if not job_ids:
        return success(data={
            "active_jobs": active_job_count,
            "total_jobs": len(jobs),
            "total_applications": 0,
            "by_status": {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0},
        })

    # 按状态分组统计投递
    rows = db.execute(
        select(JobApplication.status, func.count()).where(
            JobApplication.job_id.in_(job_ids)
        ).group_by(JobApplication.status)
    ).all()
    by_status = {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0}
    total_app = 0
    for status, cnt in rows:
        by_status[str(status)] = cnt
        total_app += cnt

    return success(data={
        "active_jobs": active_job_count,
        "total_jobs": len(jobs),
        "total_applications": total_app,
        "by_status": by_status,
    })


@router.get("/employer/trend", summary="企业投递趋势 (近14天)", response_model=None)
async def employer_application_trend(
    current_user: SysUser = Depends(require_role("ROLE_EMPLOYER", "ROLE_ADMIN")),
    db: Session = Depends(get_db),
):
    """企业投递趋势: 近 14 天每日投递量 + 各职位投递分布 Top10"""
    from datetime import datetime, timedelta

    jobs = db.execute(
        select(Job).where(Job.user_id == current_user.id)
    ).scalars().all()
    job_ids = [j.id for j in jobs]
    job_title_map = {j.id: j.title for j in jobs}

    today = datetime.utcnow().date()
    days = [(today - timedelta(days=i)) for i in range(13, -1, -1)]
    day_labels = [d.strftime("%m-%d") for d in days]
    daily_counts = {d: 0 for d in day_labels}

    job_distribution = []

    if job_ids:
        # 近 14 天每日投递量
        start_dt = datetime.combine(days[0], datetime.min.time())
        rows = db.execute(
            select(JobApplication.created_at).where(
                JobApplication.job_id.in_(job_ids),
                JobApplication.created_at >= start_dt,
            )
        ).scalars().all()
        for ts in rows:
            if ts:
                label = ts.strftime("%m-%d")
                if label in daily_counts:
                    daily_counts[label] += 1

        # 各职位投递分布 Top10
        dist_rows = db.execute(
            select(JobApplication.job_id, func.count()).where(
                JobApplication.job_id.in_(job_ids)
            ).group_by(JobApplication.job_id).order_by(func.count().desc()).limit(10)
        ).all()
        for job_id, cnt in dist_rows:
            job_distribution.append({
                "name": job_title_map.get(job_id, f"职位{job_id}"),
                "value": cnt,
            })

    return success(data={
        "days": day_labels,
        "counts": [daily_counts[d] for d in day_labels],
        "job_distribution": job_distribution,
    })
