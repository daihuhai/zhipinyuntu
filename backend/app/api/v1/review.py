"""
企业评价路由
- POST   /reviews                提交评价 (求职者, 面试结束后 status=3/4)
- GET    /reviews/company/{company_id}  企业评价列表 + 综合评分 (公开)
- GET    /reviews/my?job_id=xxx   查询当前用户是否已评价某职位 (求职者)
"""
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_role
from app.db.base import get_db
from app.models.user import SysUser
from app.models.job import Job
from app.models.application import JobApplication
from app.models.company_review import CompanyReview
from app.schemas.common import success, fail, BizError

router = APIRouter(prefix="/reviews", tags=["企业评价"])


class ReviewCreateRequest(BaseModel):
    """提交企业评价请求体"""
    company_id: int = Field(..., description="被评价企业用户ID")
    application_id: int = Field(..., description="关联投递记录ID")
    interview_score: int = Field(..., ge=1, le=5, description="面试体验 1-5")
    hr_score: int = Field(..., ge=1, le=5, description="HR响应速度 1-5")
    accuracy_score: int = Field(..., ge=1, le=5, description="职位描述准确度 1-5")
    comment: Optional[str] = Field(None, max_length=500, description="文字评价")


def _review_to_dict(r: CompanyReview) -> dict[str, Any]:
    return {
        "id": r.id,
        "company_id": r.company_id,
        "job_id": r.job_id,
        "application_id": r.application_id,
        "interview_score": r.interview_score,
        "hr_score": r.hr_score,
        "accuracy_score": r.accuracy_score,
        "comment": r.comment,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


@router.post("", summary="提交企业评价", response_model=None)
async def create_review(
    req: ReviewCreateRequest,
    current_user: SysUser = Depends(require_role("ROLE_SEEKER")),
    db: Session = Depends(get_db),
):
    """求职者面试结束后对企业进行评价 (仅面试结束状态: 3=不合适 4=已录用)"""
    # 校验投递记录归属与状态
    application = db.get(JobApplication, req.application_id)
    if application is None:
        return fail(BizError.RESOURCE_NOT_FOUND, "投递记录不存在")
    if application.applicant_id != current_user.id:
        return fail(BizError.ROLE_FORBIDDEN, "无权评价他人的投递记录")
    if application.status not in (3, 4):
        return fail(BizError.VALIDATION_ERROR, "仅面试结束(不合适/已录用)后可评价")

    # 校验被评价企业存在且是企业角色
    company = db.get(SysUser, req.company_id)
    if company is None or company.role != "ROLE_EMPLOYER":
        return fail(BizError.VALIDATION_ERROR, "被评价企业不存在")

    # 校验投递记录对应的职位属于该企业
    job = db.get(Job, application.job_id)
    if job is None or job.user_id != req.company_id:
        return fail(BizError.VALIDATION_ERROR, "该投递记录不属于被评价企业")

    # 防重复评价: 同一投递记录只能评价一次
    exists = db.execute(
        select(CompanyReview).where(CompanyReview.application_id == req.application_id)
    ).scalar_one_or_none()
    if exists is not None:
        return fail(BizError.VALIDATION_ERROR, "该投递记录已评价过, 请勿重复评价")

    try:
        review = CompanyReview(
            company_id=req.company_id,
            reviewer_id=current_user.id,
            job_id=application.job_id,
            application_id=req.application_id,
            interview_score=req.interview_score,
            hr_score=req.hr_score,
            accuracy_score=req.accuracy_score,
            comment=(req.comment or "").strip() or None,
        )
        db.add(review)
        db.commit()
        db.refresh(review)
        return success(data=_review_to_dict(review), message="评价成功, 感谢您的反馈")
    except Exception as e:
        db.rollback()
        return fail(BizError.SYSTEM_ERROR, f"评价失败: {e}")


@router.get("/company/{company_id}", summary="企业评价列表 + 综合评分", response_model=None)
async def list_company_reviews(
    company_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=50),
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取某企业的综合评分和评价列表 (公开, 评价匿名展示)"""
    company = db.get(SysUser, company_id)
    if company is None or company.role != "ROLE_EMPLOYER":
        return fail(BizError.RESOURCE_NOT_FOUND, "企业不存在")

    # 综合评分
    agg = db.execute(
        select(
            func.count(CompanyReview.id),
            func.avg(CompanyReview.interview_score),
            func.avg(CompanyReview.hr_score),
            func.avg(CompanyReview.accuracy_score),
        ).where(CompanyReview.company_id == company_id)
    ).one()
    total, avg_interview, avg_hr, avg_accuracy = agg
    total = total or 0
    avg_interview = round(float(avg_interview or 0), 1)
    avg_hr = round(float(avg_hr or 0), 1)
    avg_accuracy = round(float(avg_accuracy or 0), 1)
    overall = round((avg_interview + avg_hr + avg_accuracy) / 3, 1) if total else 0

    # 评价列表 (匿名, 仅展示维度得分 + 文字)
    offset = (page - 1) * size
    rows = db.execute(
        select(CompanyReview)
        .where(CompanyReview.company_id == company_id)
        .order_by(CompanyReview.created_at.desc())
        .offset(offset).limit(size)
    ).scalars().all()

    items = [
        {
            "job_title": (db.get(Job, r.job_id).title if r.job_id else None),
            "interview_score": r.interview_score,
            "hr_score": r.hr_score,
            "accuracy_score": r.accuracy_score,
            "comment": r.comment,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]

    return success(data={
        "company_id": company_id,
        "company_name": company.company_name or company.nickname or "企业",
        "total": total,
        "overall": overall,
        "avg_interview": avg_interview,
        "avg_hr": avg_hr,
        "avg_accuracy": avg_accuracy,
        "items": items,
    })


@router.get("/my", summary="我的评价状态 (是否已评价某职位)", response_model=None)
async def my_review_status(
    job_id: int = Query(..., description="职位ID"),
    current_user: SysUser = Depends(require_role("ROLE_SEEKER")),
    db: Session = Depends(get_db),
):
    """查询当前用户是否已评价某职位 (用于投递记录列表展示评价按钮状态)"""
    review = db.execute(
        select(CompanyReview).where(
            CompanyReview.reviewer_id == current_user.id,
            CompanyReview.job_id == job_id,
        )
    ).scalar_one_or_none()
    if review is None:
        return success(data={"reviewed": False})
    return success(data={
        "reviewed": True,
        "review_id": review.id,
        "interview_score": review.interview_score,
        "hr_score": review.hr_score,
        "accuracy_score": review.accuracy_score,
    })