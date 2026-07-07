"""
智能匹配路由
- GET /match/resume/{id}/jobs   简历推荐职位 (求职者)
- GET /match/job/{id}/resumes   职位推荐候选人 (企业)
- GET /match/history            匹配历史
"""
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_role
from app.db.base import get_db
from app.models.match import MatchRecord
from app.models.user import SysUser
from app.schemas.common import success
from app.services.match_service import match_service

router = APIRouter(prefix="/match", tags=["智能匹配"])


def _job_to_dict(job) -> dict[str, Any]:
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
async def recommend_jobs(
    resume_id: int,
    top_k: int = Query(10, ge=1, le=50),
    current_user: SysUser = Depends(require_role("ROLE_SEEKER", "ROLE_ADMIN")),
    db: Session = Depends(get_db),
):
    """为求职者简历推荐匹配职位 (召回→粗排→精排)"""
    results = match_service.recommend_jobs_for_resume(resume_id, db, top_k=top_k)
    data = [
        {
            "job": _job_to_dict(item["job"]),
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
    return success(data={"items": data, "total": len(data)})


@router.get("/job/{job_id}/resumes", summary="职位推荐候选人")
async def recommend_resumes(
    job_id: int,
    top_k: int = Query(10, ge=1, le=50),
    current_user: SysUser = Depends(require_role("ROLE_EMPLOYER", "ROLE_ADMIN")),
    db: Session = Depends(get_db),
):
    """为企业职位推荐匹配候选人 (召回→粗排→精排)"""
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
        }
        for item in results
    ]
    return success(data={"items": data, "total": len(data)})


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
