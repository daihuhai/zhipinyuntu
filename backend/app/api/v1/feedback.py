"""用户反馈 API"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc, func, or_
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_admin
from app.db.base import get_db
from app.models.user import SysUser
from app.models.feedback import Feedback
from app.models.message import Message
from app.schemas.feedback import FeedbackCreate, FeedbackReply
from app.schemas.common import success, fail, BizError

router = APIRouter(prefix="/feedback", tags=["反馈"])

TYPE_LABEL = {"bug": "Bug报告", "feature": "功能建议", "other": "其他"}
STATUS_LABEL = {"pending": "待处理", "processing": "处理中", "resolved": "已解决"}


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

    return success(data={
        "total": total,
        "items": [{
            "id": f.id,
            "type": f.type,
            "type_label": TYPE_LABEL.get(f.type, f.type),
            "title": f.title,
            "content": f.content,
            "status": f.status,
            "status_label": STATUS_LABEL.get(f.status, f.status),
            "admin_reply": f.admin_reply,
            "created_at": f.created_at.isoformat() if f.created_at else None,
            "updated_at": f.updated_at.isoformat() if f.updated_at else None,
        } for f in items],
    })


@router.get("/my-stats", summary="我的反馈统计")
async def my_feedback_stats(
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户各状态反馈数量"""
    total = db.execute(select(func.count(Feedback.id)).where(Feedback.user_id == current_user.id)).scalar() or 0
    pending = db.execute(select(func.count(Feedback.id)).where(
        Feedback.user_id == current_user.id, Feedback.status == "pending"
    )).scalar() or 0
    processing = db.execute(select(func.count(Feedback.id)).where(
        Feedback.user_id == current_user.id, Feedback.status == "processing"
    )).scalar() or 0
    resolved = db.execute(select(func.count(Feedback.id)).where(
        Feedback.user_id == current_user.id, Feedback.status == "resolved"
    )).scalar() or 0
    return success(data={
        "total": total,
        "pending": pending,
        "processing": processing,
        "resolved": resolved,
    })


# ===== 管理员接口 =====
admin_router = APIRouter(prefix="/admin/feedbacks", tags=["管理员-反馈管理"])


@admin_router.get("", summary="管理员查看所有反馈")
async def admin_list_feedbacks(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: str | None = Query(None, description="筛选: pending/processing/resolved"),
    type: str | None = Query(None, description="筛选: bug/feature/other"),
    keyword: str | None = Query(None, description="关键词搜索(标题/内容)"),
    admin: SysUser = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """管理员查看所有反馈"""
    q = select(Feedback)
    count_q = select(func.count(Feedback.id))

    if status:
        q = q.where(Feedback.status == status)
        count_q = count_q.where(Feedback.status == status)
    if type:
        q = q.where(Feedback.type == type)
        count_q = count_q.where(Feedback.type == type)
    if keyword:
        kw = f"%{keyword}%"
        q = q.where(or_(Feedback.title.like(kw), Feedback.content.like(kw)))
        count_q = count_q.where(or_(Feedback.title.like(kw), Feedback.content.like(kw)))

    total = db.execute(count_q).scalar() or 0
    items = db.execute(
        q.order_by(desc(Feedback.created_at)).offset((page - 1) * size).limit(size)
    ).scalars().all()

    # 批量查用户信息避免 N+1
    user_ids = {f.user_id for f in items}
    users = {u.id: u for u in db.execute(select(SysUser).where(SysUser.id.in_(user_ids))).scalars().all()} if user_ids else {}

    return success(data={
        "total": total,
        "items": [{
            "id": f.id,
            "user_id": f.user_id,
            "username": users[f.user_id].username if f.user_id in users else "",
            "role": users[f.user_id].role if f.user_id in users else "",
            "type": f.type,
            "type_label": TYPE_LABEL.get(f.type, f.type),
            "title": f.title,
            "content": f.content,
            "status": f.status,
            "status_label": STATUS_LABEL.get(f.status, f.status),
            "admin_reply": f.admin_reply,
            "created_at": f.created_at.isoformat() if f.created_at else None,
            "updated_at": f.updated_at.isoformat() if f.updated_at else None,
        } for f in items],
    })


@admin_router.get("/stats", summary="管理员反馈统计")
async def admin_feedback_stats(
    admin: SysUser = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """获取全平台反馈统计"""
    total = db.execute(select(func.count(Feedback.id))).scalar() or 0
    pending = db.execute(select(func.count(Feedback.id)).where(Feedback.status == "pending")).scalar() or 0
    processing = db.execute(select(func.count(Feedback.id)).where(Feedback.status == "processing")).scalar() or 0
    resolved = db.execute(select(func.count(Feedback.id)).where(Feedback.status == "resolved")).scalar() or 0
    return success(data={
        "total": total,
        "pending": pending,
        "processing": processing,
        "resolved": resolved,
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

    # 如果勾选通知, 创建站内消息
    if req.notify:
        status_text = STATUS_LABEL.get(req.status, req.status)
        content = f"您提交的反馈「{fb.title}」已被管理员处理，状态更新为：{status_text}。"
        if req.reply:
            content += f"\n回复内容：{req.reply}"
        msg = Message(
            sender_id=admin.id,
            receiver_id=fb.user_id,
            content=content,
            is_read=0,
        )
        db.add(msg)
        db.commit()

    return success(message="处理成功")
