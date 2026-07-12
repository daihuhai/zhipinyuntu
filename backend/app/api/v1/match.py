"""
智能匹配路由
- GET /match/resume/{id}/jobs   简历推荐职位 (求职者)
- GET /match/job/{id}/resumes   职位推荐候选人 (企业)
- GET /match/history            匹配历史
"""
from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.deps import get_current_user, require_role
from app.core.limiter import limiter
from app.db.base import get_db
from app.models.match import MatchRecord
from app.models.user import SysUser
from app.models.job import Job
from app.models.resume import Resume
from app.schemas.common import success, fail, BizError
from app.services.match_service import match_service

router = APIRouter(prefix="/match", tags=["智能匹配"])


def _job_to_dict(job, application_count: int = 0) -> dict[str, Any]:
    return {
        "id": job.id,
        "title": job.title,
        "company": job.company,
        "work_city": job.work_city,
        "salary_min": job.salary_min,
        "salary_max": job.salary_max,
        "experience_required": job.experience_required,
        "education_required": job.education_required,
        "description": (job.description or "")[:300],
        "requirements": [
            {"skill_name": r.skill_name, "req_type": r.req_type}
            for r in job.requirements
        ],
        "application_count": application_count,
    }


def _resume_to_dict(resume) -> dict[str, Any]:
    return {
        "id": resume.id,
        "name": resume.name,
        "gender": resume.gender,
        "age": resume.age,
        "education": resume.education,
        "school": resume.school,
        "major": resume.major,
        "work_years": resume.work_years,
        "current_city": resume.current_city,
        "expected_salary_min": resume.expected_salary_min,
        "expected_salary_max": resume.expected_salary_max,
        "skills": [
            {"skill_name": s.skill_name, "skill_level": s.skill_level}
            for s in resume.skills
        ],
        "self_evaluation": (resume.self_evaluation or "")[:300],
    }


@router.get("/resume/{resume_id}/jobs", summary="简历推荐职位")
@limiter.limit("10/minute")
def recommend_jobs(
    request: Request,
    resume_id: int,
    top_k: int = Query(10, ge=1, le=50),
    current_user: SysUser = Depends(require_role("ROLE_SEEKER", "ROLE_ADMIN")),
    db: Session = Depends(get_db),
):
    """为求职者简历推荐匹配职位 (召回→粗排→精排)"""
    from sqlalchemy import func

    resume = db.get(Resume, resume_id)
    if not resume:
        results = match_service.recommend_jobs_cold_start(current_user.id, db, top_k=top_k)
    else:
        results = match_service.recommend_jobs_for_resume(resume_id, db, top_k=top_k)

    # 批量查询职位的投递数
    job_ids = [item["job"].id for item in results]
    app_counts = {}
    if job_ids:
        from app.models.application import JobApplication
        rows = db.execute(
            select(JobApplication.job_id, func.count())
            .where(JobApplication.job_id.in_(job_ids))
            .group_by(JobApplication.job_id)
        ).all()
        app_counts = {jid: cnt for jid, cnt in rows}

    data = [
        {
            "job": _job_to_dict(item["job"], application_count=app_counts.get(item["job"].id, 0)),
            "total_score": item["total_score"],
            "skill_score": item["skill_score"],
            "exp_score": item["exp_score"],
            "edu_score": item["edu_score"],
            "city_score": item["city_score"],
            "salary_score": item["salary_score"],
            "proj_score": item["proj_score"],
            "match_reason": item["match_reason"],
        }
        for item in results
    ]

    # 记录 AI 匹配操作日志
    try:
        from app.services.admin_service import admin_service
        admin_service.write_system_log(
            db,
            action="AI_MATCH_RECOMMEND",
            target_type="resume",
            target_id=resume_id,
            detail=f"大模型推荐职位: 简历ID={resume_id}, 返回{len(data)}条结果",
        )
    except Exception:
        pass

    return success(data={"items": data, "total": len(data)})


@router.get("/job/{job_id}/resumes", summary="职位推荐候选人")
@limiter.limit("10/minute")
def recommend_resumes(
    request: Request,
    job_id: int,
    top_k: int = Query(10, ge=1, le=50),
    current_user: SysUser = Depends(require_role("ROLE_EMPLOYER", "ROLE_ADMIN")),
    db: Session = Depends(get_db),
):
    """为企业职位推荐匹配候选人 (召回→粗排→精排)"""
    # IDOR 防护: 企业仅可查看本企业职位的候选人 (管理员除外)
    job = db.get(Job, job_id)
    if not job:
        return fail(BizError.RESOURCE_NOT_FOUND, "职位不存在")
    if current_user.role == "ROLE_EMPLOYER" and job.user_id != current_user.id:
        return fail(BizError.ROLE_FORBIDDEN, "无权查看非本企业职位的候选人")

    results = match_service.recommend_resumes_for_job(job_id, db, top_k=top_k)
    data = [
        {
            "resume": _resume_to_dict(item["resume"]),
            "total_score": item["total_score"],
            "skill_score": item["skill_score"],
            "exp_score": item["exp_score"],
            "edu_score": item["edu_score"],
            "city_score": item["city_score"],
            "salary_score": item["salary_score"],
            "proj_score": item["proj_score"],
            "match_reason": item["match_reason"],
            "application_id": item.get("application_id"),
            "application_status": item.get("application_status"),
        }
        for item in results
    ]

    # 记录 AI 匹配操作日志
    try:
        from app.services.admin_service import admin_service
        admin_service.write_system_log(
            db,
            action="AI_MATCH_RECOMMEND",
            target_type="job",
            target_id=job_id,
            detail=f"大模型推荐候选人: 职位ID={job_id}, 返回{len(data)}条结果",
        )
    except Exception:
        pass

    return success(data={"items": data, "total": len(data)})


@router.get("/score", summary="获取简历与岗位的匹配分")
@limiter.limit("30/minute")
def get_match_score(
    request: Request,
    resume_id: int = Query(..., description="简历ID"),
    job_id: int = Query(..., description="职位ID"),
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取简历与岗位的六维度匹配分 (统一匹配度数据源)

    匹配度主体是简历(resume), 不是用户(user)。
    同一用户的多份简历对同一岗位的匹配度不同。
    仅调用粗排(纯规则计算), 不触发 LLM 精排, 响应 < 100ms。
    """
    # 预加载 skills 关系, 避免懒加载失败导致技能维度评分为 0
    resume = db.execute(
        select(Resume)
        .options(selectinload(Resume.skills))
        .where(Resume.id == resume_id)
    ).scalar_one_or_none()
    job = db.execute(
        select(Job)
        .options(selectinload(Job.requirements))
        .where(Job.id == job_id)
    ).scalar_one_or_none()
    if not resume or not job:
        return fail(BizError.RESOURCE_NOT_FOUND, "简历或职位不存在")

    # 调用匹配引擎粗排 (六维度评分, 纯计算无 LLM 调用)
    scores = match_service.coarse_rank(resume, job)

    return success(data={
        "total_score": scores["total"],
        "skill_score": scores["skill"],
        "experience_score": scores["experience"],
        "education_score": scores["education"],
        "city_score": scores["city"],
        "salary_score": scores["salary"],
        "project_score": scores["project"],
    })


@router.get("/history", summary="匹配历史记录")
async def match_history(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    direction: str | None = Query(None, description="RESUME_TO_JOB/JOB_TO_RESUME"),
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """查询匹配历史记录"""
    stmt = select(MatchRecord)
    if direction:
        stmt = stmt.where(MatchRecord.direction == direction)
    stmt = stmt.order_by(MatchRecord.created_at.desc())

    total = len(list(db.execute(stmt).scalars()))
    offset = (page - 1) * size
    items = list(db.execute(stmt.offset(offset).limit(size)).scalars())
    data = [
        {
            "id": m.id,
            "resume_id": m.resume_id,
            "job_id": m.job_id,
            "total_score": m.total_score,
            "skill_score": m.skill_score,
            "exp_score": m.exp_score,
            "edu_score": m.edu_score,
            "city_score": m.city_score,
            "salary_score": m.salary_score,
            "proj_score": m.proj_score,
            "match_reason": m.match_reason,
            "direction": m.direction,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in items
    ]
    return success(data={"items": data, "total": total, "page": page, "size": size})
