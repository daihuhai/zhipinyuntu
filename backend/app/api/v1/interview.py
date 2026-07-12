"""面试邀请路由"""
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, field_validator
from sqlalchemy import select, func
from sqlalchemy.orm import Session, selectinload

from app.core.deps import require_role
from app.db.base import get_db
from app.models.user import SysUser
from app.models.job import Job
from app.models.resume import Resume
from app.models.application import JobApplication
from app.models.interview import Interview
from app.schemas.common import success, fail, BizError

router = APIRouter(prefix="/interviews", tags=["面试邀请"])


class InterviewCreateRequest(BaseModel):
    application_id: int
    interview_time: str
    location: Optional[str] = None
    interview_type: str = "线下"
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    remark: Optional[str] = None

    @field_validator("interview_type")
    @classmethod
    def check_type(cls, v: str) -> str:
        if v not in ("线下", "线上", "电话"):
            raise ValueError("面试形式只能为 线下/线上/电话")
        return v


@router.post("", summary="企业创建面试邀请", response_model=None)
async def create_interview(
    req: InterviewCreateRequest,
    current_user: SysUser = Depends(require_role("ROLE_EMPLOYER", "ROLE_ADMIN")),
    db: Session = Depends(get_db),
):
    """企业创建面试邀请, 同时更新投递状态为'面试邀请'"""
    app = db.get(JobApplication, req.application_id)
    if not app:
        return fail(BizError.RESOURCE_NOT_FOUND, "投递记录不存在")

    # IDOR 防护
    job = db.get(Job, app.job_id)
    if current_user.role == "ROLE_EMPLOYER" and (not job or job.user_id != current_user.id):
        return fail(BizError.ROLE_FORBIDDEN, "无权操作非本企业职位的投递记录")

    # 校验是否已存在面试邀请
    existing = db.execute(
        select(Interview).where(Interview.application_id == req.application_id)
    ).scalar_one_or_none()
    if existing:
        return fail(BizError.VALIDATION_ERROR, "已存在面试邀请, 请勿重复创建")

    try:
        interview_time = datetime.fromisoformat(req.interview_time)
    except ValueError:
        return fail(BizError.VALIDATION_ERROR, "面试时间格式错误 (ISO 8601)")

    try:
        interview = Interview(
            application_id=req.application_id,
            employer_id=current_user.id,
            seeker_id=app.applicant_id,
            interview_time=interview_time,
            location=req.location,
            interview_type=req.interview_type,
            contact_person=req.contact_person,
            contact_phone=req.contact_phone,
            remark=req.remark,
            status=0,
        )
        db.add(interview)
        app.status = 2  # 更新投递状态为面试邀请
        db.commit()
        db.refresh(interview)
        return success(data={"id": interview.id}, message="面试邀请已发送")
    except Exception as e:
        db.rollback()
        return fail(BizError.SYSTEM_ERROR, f"创建失败: {e}")


@router.get("/seeker", summary="求职者面试邀请列表", response_model=None)
async def seeker_interviews(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: SysUser = Depends(require_role("ROLE_SEEKER", "ROLE_ADMIN")),
    db: Session = Depends(get_db),
):
    """求职者查看收到的面试邀请 (含职位信息)"""
    total = db.execute(
        select(func.count()).select_from(Interview).where(Interview.seeker_id == current_user.id)
    ).scalar_one()

    rows = db.execute(
        select(Interview)
        .where(Interview.seeker_id == current_user.id)
        .order_by(Interview.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    ).scalars().all()

    items = []
    for inv in rows:
        app = db.get(JobApplication, inv.application_id)
        job = db.get(Job, app.job_id) if app else None
        items.append({
            "id": inv.id,
            "application_id": inv.application_id,
            "interview_time": inv.interview_time.isoformat() if inv.interview_time else None,
            "location": inv.location,
            "interview_type": inv.interview_type,
            "contact_person": inv.contact_person,
            "contact_phone": inv.contact_phone,
            "remark": inv.remark,
            "status": inv.status,
            "created_at": inv.created_at.isoformat() if inv.created_at else None,
            "job": {
                "id": job.id, "title": job.title, "company": job.company,
                "work_city": job.work_city,
            } if job else None,
        })
    return success(data={"items": items, "total": total, "page": page, "size": size})


@router.get("/employer", summary="企业已发送面试邀请", response_model=None)
async def employer_interviews(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: SysUser = Depends(require_role("ROLE_EMPLOYER", "ROLE_ADMIN")),
    db: Session = Depends(get_db),
):
    """企业查看已发送的面试邀请"""
    total = db.execute(
        select(func.count()).select_from(Interview).where(Interview.employer_id == current_user.id)
    ).scalar_one()

    rows = db.execute(
        select(Interview)
        .where(Interview.employer_id == current_user.id)
        .order_by(Interview.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    ).scalars().all()

    items = []
    for inv in rows:
        app = db.get(JobApplication, inv.application_id)
        job = db.get(Job, app.job_id) if app else None
        items.append({
            "id": inv.id,
            "application_id": inv.application_id,
            "interview_time": inv.interview_time.isoformat() if inv.interview_time else None,
            "location": inv.location,
            "interview_type": inv.interview_type,
            "contact_person": inv.contact_person,
            "contact_phone": inv.contact_phone,
            "remark": inv.remark,
            "status": inv.status,
            "created_at": inv.created_at.isoformat() if inv.created_at else None,
            "job": {
                "id": job.id, "title": job.title, "company": job.company,
            } if job else None,
        })
    return success(data={"items": items, "total": total, "page": page, "size": size})


@router.post("/{interview_id}/accept", summary="求职者接受面试", response_model=None)
async def accept_interview(
    interview_id: int,
    current_user: SysUser = Depends(require_role("ROLE_SEEKER", "ROLE_ADMIN")),
    db: Session = Depends(get_db),
):
    """求职者接受面试邀请"""
    inv = db.get(Interview, interview_id)
    if not inv:
        return fail(BizError.RESOURCE_NOT_FOUND, "面试邀请不存在")
    if current_user.role == "ROLE_SEEKER" and inv.seeker_id != current_user.id:
        return fail(BizError.ROLE_FORBIDDEN, "无权操作他人的面试邀请")
    if inv.status != 0:
        return fail(BizError.VALIDATION_ERROR, "该面试邀请已处理")

    inv.status = 1
    db.commit()
    return success(message="已接受面试邀请")


@router.post("/{interview_id}/reject", summary="求职者拒绝面试", response_model=None)
async def reject_interview(
    interview_id: int,
    current_user: SysUser = Depends(require_role("ROLE_SEEKER", "ROLE_ADMIN")),
    db: Session = Depends(get_db),
):
    """求职者拒绝面试邀请"""
    inv = db.get(Interview, interview_id)
    if not inv:
        return fail(BizError.RESOURCE_NOT_FOUND, "面试邀请不存在")
    if current_user.role == "ROLE_SEEKER" and inv.seeker_id != current_user.id:
        return fail(BizError.ROLE_FORBIDDEN, "无权操作他人的面试邀请")
    if inv.status != 0:
        return fail(BizError.VALIDATION_ERROR, "该面试邀请已处理")

    inv.status = 2
    db.commit()
    return success(message="已拒绝面试邀请")