"""
消息路由
- POST   /messages              发送消息
- GET    /messages/conversations 会话列表 (按对方分组)
- GET    /messages/with/{user_id} 与某人的消息记录
- POST   /messages/{id}/read    标记已读
- GET    /messages/unread-count  未读消息数
"""
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select, func, or_, and_
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.base import get_db
from app.models.user import SysUser
from app.models.message import Message
from app.schemas.common import success, fail, BizError

router = APIRouter(prefix="/messages", tags=["消息"])


class SendMessageRequest(BaseModel):
    """发送消息请求体"""
    receiver_id: int
    content: str
    job_id: Optional[int] = None


def _message_to_dict(msg: Message, sender: SysUser | None = None) -> dict[str, Any]:
    return {
        "id": msg.id,
        "sender_id": msg.sender_id,
        "receiver_id": msg.receiver_id,
        "job_id": msg.job_id,
        "content": msg.content,
        "is_read": msg.is_read,
        "created_at": msg.created_at.isoformat() if msg.created_at else None,
        "sender_name": sender.nickname if sender else None,
        "sender_role": sender.role if sender else None,
    }


@router.post("", summary="发送消息", response_model=None)
async def send_message(
    req: SendMessageRequest,
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """发送消息给其他用户 (求职者 ↔ 企业)"""
    if req.receiver_id == current_user.id:
        return fail(BizError.VALIDATION_ERROR, "不能给自己发消息")
    if not req.content.strip():
        return fail(BizError.VALIDATION_ERROR, "消息内容不能为空")

    receiver = db.get(SysUser, req.receiver_id)
    if receiver is None:
        return fail(BizError.RESOURCE_NOT_FOUND, "接收方用户不存在")

    try:
        msg = Message(
            sender_id=current_user.id,
            receiver_id=req.receiver_id,
            job_id=req.job_id,
            content=req.content.strip(),
            is_read=0,
        )
        db.add(msg)
        db.commit()
        db.refresh(msg)
        return success(data=_message_to_dict(msg, current_user), message="发送成功")
    except Exception as e:
        db.rollback()
        return fail(BizError.SYSTEM_ERROR, f"发送失败: {e}")


@router.get("/conversations", summary="会话列表", response_model=None)
async def list_conversations(
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户的会话列表 (按对方分组, 显示最后一条消息)"""
    # 查询所有涉及当前用户的消息
    msgs = db.execute(
        select(Message).where(
            or_(Message.sender_id == current_user.id, Message.receiver_id == current_user.id)
        ).order_by(Message.created_at.desc())
    ).scalars().all()

    # 按对方用户分组
    conv_map: dict[int, dict] = {}
    for msg in msgs:
        other_id = msg.receiver_id if msg.sender_id == current_user.id else msg.sender_id
        if other_id not in conv_map:
            # 查询对方用户信息
            other_user = db.get(SysUser, other_id)
            # 统计未读数
            unread = sum(1 for m in msgs if m.sender_id == other_id and m.receiver_id == current_user.id and m.is_read == 0)
            conv_map[other_id] = {
                "user_id": other_id,
                "user_name": other_user.nickname if other_user else f"用户{other_id}",
                "user_role": other_user.role if other_user else None,
                "last_message": msg.content[:50],
                "last_time": msg.created_at.isoformat() if msg.created_at else None,
                "unread_count": unread,
            }
        else:
            # 更新未读数
            if msg.sender_id == other_id and msg.receiver_id == current_user.id and msg.is_read == 0:
                conv_map[other_id]["unread_count"] += 1

    # 按最后消息时间排序
    conv_list = sorted(conv_map.values(), key=lambda x: x["last_time"] or "", reverse=True)
    return success(data={"items": conv_list, "total": len(conv_list)})


@router.get("/with/{user_id}", summary="与某人的消息记录", response_model=None)
async def list_messages_with_user(
    user_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取与某用户的消息记录 (按时间正序)"""
    base_stmt = select(Message, SysUser).join(
        SysUser, Message.sender_id == SysUser.id
    ).where(
        or_(
            and_(Message.sender_id == current_user.id, Message.receiver_id == user_id),
            and_(Message.sender_id == user_id, Message.receiver_id == current_user.id),
        )
    )

    total = db.execute(
        select(func.count()).select_from(Message).where(
            or_(
                and_(Message.sender_id == current_user.id, Message.receiver_id == user_id),
                and_(Message.sender_id == user_id, Message.receiver_id == current_user.id),
            )
        )
    ).scalar_one()

    offset = (page - 1) * size
    rows = db.execute(
        base_stmt.order_by(Message.created_at.desc()).offset(offset).limit(size)
    ).all()

    # 反转为正序 (旧→新)
    items = [_message_to_dict(msg, sender) for msg, sender in reversed(rows)]

    # 自动标记收到的消息为已读
    unread_msgs = db.execute(
        select(Message).where(
            Message.sender_id == user_id,
            Message.receiver_id == current_user.id,
            Message.is_read == 0,
        )
    ).scalars().all()
    for msg in unread_msgs:
        msg.is_read = 1
    db.commit()

    # 获取对方用户信息
    other_user = db.get(SysUser, user_id)
    other_info = {
        "user_id": user_id,
        "user_name": other_user.nickname if other_user else f"用户{user_id}",
        "user_role": other_user.role if other_user else None,
    }

    return success(data={"items": items, "total": total, "other": other_info})


@router.post("/{message_id}/read", summary="标记消息已读", response_model=None)
async def mark_message_read(
    message_id: int,
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """标记消息为已读"""
    msg = db.get(Message, message_id)
    if msg is None:
        return fail(BizError.RESOURCE_NOT_FOUND, "消息不存在")
    if msg.receiver_id != current_user.id:
        return fail(BizError.ROLE_FORBIDDEN, "无权操作此消息")

    msg.is_read = 1
    db.commit()
    return success(data={"id": msg.id, "is_read": 1}, message="已标记为已读")


@router.get("/unread-count", summary="未读消息数", response_model=None)
async def get_unread_count(
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户的未读消息总数"""
    count = db.execute(
        select(func.count()).select_from(Message).where(
            Message.receiver_id == current_user.id,
            Message.is_read == 0,
        )
    ).scalar_one()
    return success(data={"unread_count": count})
