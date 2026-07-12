"""职位订阅路由"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import require_role
from app.db.base import get_db
from app.models.user import SysUser
from app.models.subscription import JobSubscription
from app.schemas.common import success, fail, BizError

router = APIRouter(prefix="/subscriptions", tags=["职位订阅"])


class SubscriptionRequest(BaseModel):
    cities: str | None = None
    job_types: str | None = None
    keywords: str | None = None
    enabled: int = 1


@router.post("", summary="创建/更新订阅", response_model=None)
async def upsert_subscription(
    req: SubscriptionRequest,
    current_user: SysUser = Depends(require_role("ROLE_SEEKER", "ROLE_ADMIN")),
    db: Session = Depends(get_db),
):
    """创建或更新职位订阅 (每个用户仅保留一条)"""
    sub = db.execute(
        select(JobSubscription).where(JobSubscription.user_id == current_user.id)
    ).scalar_one_or_none()

    try:
        if sub:
            sub.cities = req.cities
            sub.job_types = req.job_types
            sub.keywords = req.keywords
            sub.enabled = req.enabled
        else:
            sub = JobSubscription(
                user_id=current_user.id,
                cities=req.cities,
                job_types=req.job_types,
                keywords=req.keywords,
                enabled=req.enabled,
            )
            db.add(sub)
        db.commit()
        db.refresh(sub)
        return success(data={"id": sub.id}, message="订阅设置已保存")
    except Exception as e:
        db.rollback()
        return fail(BizError.SYSTEM_ERROR, f"保存失败: {e}")


@router.get("", summary="获取当前订阅", response_model=None)
async def get_subscription(
    current_user: SysUser = Depends(require_role("ROLE_SEEKER", "ROLE_ADMIN")),
    db: Session = Depends(get_db),
):
    """获取当前用户的职位订阅设置"""
    sub = db.execute(
        select(JobSubscription).where(JobSubscription.user_id == current_user.id)
    ).scalar_one_or_none()
    if not sub:
        return success(data=None, message="暂未设置订阅")
    return success(data={
        "id": sub.id,
        "cities": sub.cities,
        "job_types": sub.job_types,
        "keywords": sub.keywords,
        "enabled": sub.enabled,
        "created_at": sub.created_at.isoformat() if sub.created_at else None,
    })


@router.delete("", summary="取消订阅", response_model=None)
async def delete_subscription(
    current_user: SysUser = Depends(require_role("ROLE_SEEKER", "ROLE_ADMIN")),
    db: Session = Depends(get_db),
):
    """取消当前用户的职位订阅"""
    sub = db.execute(
        select(JobSubscription).where(JobSubscription.user_id == current_user.id)
    ).scalar_one_or_none()
    if not sub:
        return fail(BizError.RESOURCE_NOT_FOUND, "暂无订阅记录")
    try:
        db.delete(sub)
        db.commit()
        return success(message="订阅已取消")
    except Exception as e:
        db.rollback()
        return fail(BizError.SYSTEM_ERROR, f"取消失败: {e}")