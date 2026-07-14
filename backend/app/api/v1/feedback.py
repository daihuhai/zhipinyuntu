"""用户反馈 API"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc, func
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_admin
from app.db.base import get_db
from app.models.user import SysUser
from app.models.feedback import Feedback
from app.schemas.feedback import FeedbackCreate, FeedbackReply
from app.schemas.common import success, fail, BizError

router = APIRouter(prefix="/feedback", tags=["反馈"])


@router.post("", summary="提交反馈")
async def create_feedback(
    req: FeedbackCreate,
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """用户提交反馈"""
    feedback = Feedback(
        user_id=current_user.id,
        type=req.type,
        title=req.title,
        content=req.content,
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return success(data={"id": feedback.id}, message="反馈提交成功")


@router.get("/my", summary="我的反馈列表")
async def my_feedbacks(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=50),
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """查看我提交的反馈"""
    total = db.execute(
        select(func.count(Feedback.id)).where(Feedback.user_id == current_user.id)
    ).scalar() or 0
    items = db.execute(
        select(Feedback)
        .where(Feedback.user_id == current_user.id)
        .order_by(desc(Feedback.created_at))
        .offset((page - 1) * size)
        .limit(size)
    ).scalars().all()

    type_label = {"bug": "Bug报告", "feature": "功能建议", "other": "其他"}
    status_label = {"pending": "待处理", "processing": "处理中", "resolved": "已解决"}
    return success(data={
        "total": total,
        "items": [{
            "id": f.id,
            "type": f.type,
            "type_label": type_label.get(f.type, f.type),
            "title": f.title,
            "content": f.content,
            "status": f.status,
            "status_label": status_label.get(f.status, f.status),
            "admin_reply": f.admin_reply,
            "created_at": f.created_at.isoformat() if f.created_at else None,
            "updated_at": f.updated_at.isoformat() if f.updated_at else None,
        } for f in items],
    })


# ===== 管理员接口 =====
admin_router = APIRouter(prefix="/admin/feedbacks", tags=["管理员-反馈管理"])


@admin_router.get("", summary="管理员查看所有反馈")
async def admin_list_feedbacks(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: str | None = Query(None, description="筛选: pending/processing/resolved"),
    admin: SysUser = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """管理员查看所有反馈"""
    q = select(Feedback)
    if status:
        q = q.where(Feedback.status == status)
    total = db.execute(select(func.count(Feedback.id))).scalar() or 0
    items = db.execute(
        q.order_by(desc(Feedback.created_at)).offset((page - 1) * size).limit(size)
    ).scalars().all()

    type_label = {"bug": "Bug报告", "feature": "功能建议", "other": "其他"}
    status_label = {"pending": "待处理", "processing": "处理中", "resolved": "已解决"}
    return success(data={
        "total": total,
        "items": [{
            "id": f.id,
            "user_id": f.user_id,
            "type": f.type,
            "type_label": type_label.get(f.type, f.type),
            "title": f.title,
            "content": f.content,
            "status": f.status,
            "status_label": status_label.get(f.status, f.status),
            "admin_reply": f.admin_reply,
            "created_at": f.created_at.isoformat() if f.created_at else None,
            "updated_at": f.updated_at.isoformat() if f.updated_at else None,
        } for f in items],
    })


@admin_router.put("/{feedback_id}", summary="管理员处理反馈")
async def admin_reply_feedback(
    feedback_id: int,
    req: FeedbackReply,
    admin: SysUser = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """管理员回复/更新反馈状态"""
    fb = db.get(Feedback, feedback_id)
    if not fb:
        return fail(BizError.NOT_FOUND, "反馈不存在")
    fb.status = req.status
    fb.admin_reply = req.reply
    fb.admin_id = admin.id
    db.commit()
    return success(message="处理成功")