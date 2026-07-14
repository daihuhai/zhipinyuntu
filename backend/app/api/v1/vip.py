"""
VIP 会员路由
- GET  /vip/quota           获取当前配额信息
- GET  /vip/plans           获取 VIP 套餐列表
- POST /vip/recharge        VIP 充值 (模拟微信/支付宝支付)
- POST /vip/buy-single      购买单次付费额度 (模拟支付)
- POST /vip/pay/confirm     支付回调确认 (模拟)
"""
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from typing import Literal
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_role
from app.core.limiter import limiter
from app.db.base import get_db
from app.models.user import SysUser
from app.schemas.common import success, fail, BizError
from app.services.vip_service import vip_service, VIP_PLANS, SINGLE_PAY_PRICE

router = APIRouter(prefix="/vip", tags=["VIP 会员"])


class RechargeRequest(BaseModel):
    """VIP 充值请求"""
    plan: Literal["monthly", "quarterly", "yearly"] = Field(..., description="套餐类型")
    pay_method: Literal["wechat", "alipay"] = Field(..., description="支付方式: wechat/alipay")


class BuySingleRequest(BaseModel):
    """单次付费请求"""
    count: int = Field(1, ge=1, le=100, description="购买次数")
    pay_method: Literal["wechat", "alipay"] = Field(..., description="支付方式: wechat/alipay")


class PayConfirmRequest(BaseModel):
    """支付确认请求 (模拟支付平台回调)"""
    order_id: str = Field(..., description="订单号")


# 模拟订单存储 (生产环境应使用数据库或 Redis)
_pending_orders: dict[str, dict] = {}


@router.get("/quota", summary="获取当前配额信息", response_model=None)
async def get_quota(current_user: SysUser = Depends(get_current_user)):
    """获取当前用户的 VIP 状态和配额信息"""
    quota = vip_service.get_quota_info(current_user)
    return success(data=quota)


@router.get("/plans", summary="获取 VIP 套餐列表", response_model=None)
async def get_plans():
    """获取 VIP 套餐和单次付费价格"""
    plans = [
        {
            "key": k,
            "name": v["name"],
            "price": v["price"],
            "price_yuan": f"{v['price']/100:.2f}",
            "duration_days": v["duration_days"],
            "desc": v["desc"],
        }
        for k, v in VIP_PLANS.items()
    ]
    return success(data={
        "vip_plans": plans,
        "single_pay_price": SINGLE_PAY_PRICE,
        "single_pay_yuan": f"{SINGLE_PAY_PRICE/100:.2f}",
        "free_quota_limit": 2,
    })


@router.post("/recharge", summary="VIP 充值 (创建订单)", response_model=None)
@limiter.limit("10/minute")
async def recharge(
    request: Request,
    req: RechargeRequest,
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """VIP 充值 - 创建支付订单 (模拟微信/支付宝支付)

    前端流程:
    1. 调用此接口创建订单, 获取 order_id 和支付链接
    2. 展示支付二维码 (模拟)
    3. 用户"完成支付"后调用 /vip/pay/confirm 确认
    4. 确认后 VIP 自动激活
    """
    plan_info = VIP_PLANS[req.plan]
    order_id = f"VIP{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6].upper()}"

    # 模拟支付链接
    pay_url = f"https://pay.mock.zhipinyuntu.com/order/{order_id}"

    _pending_orders[order_id] = {
        "user_id": current_user.id,
        "type": "vip_recharge",
        "plan": req.plan,
        "amount": plan_info["price"],
        "pay_method": req.pay_method,
        "status": "pending",
        "created_at": datetime.utcnow().isoformat(),
    }

    return success(data={
        "order_id": order_id,
        "pay_url": pay_url,
        "amount": plan_info["price"],
        "amount_yuan": f"{plan_info['price']/100:.2f}",
        "pay_method": req.pay_method,
        "plan_name": plan_info["name"],
        "message": f"订单创建成功, 请使用{'微信' if req.pay_method == 'wechat' else '支付宝'}扫码支付 {plan_info['price']/100:.2f} 元",
    })


@router.post("/buy-single", summary="购买单次付费 (创建订单)", response_model=None)
@limiter.limit("10/minute")
async def buy_single(
    request: Request,
    req: BuySingleRequest,
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """购买单次付费额度 - 创建支付订单 (模拟微信/支付宝支付)"""
    amount = SINGLE_PAY_PRICE * req.count
    order_id = f"SGL{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6].upper()}"

    pay_url = f"https://pay.mock.zhipinyuntu.com/order/{order_id}"

    _pending_orders[order_id] = {
        "user_id": current_user.id,
        "type": "single_pay",
        "count": req.count,
        "amount": amount,
        "pay_method": req.pay_method,
        "status": "pending",
        "created_at": datetime.utcnow().isoformat(),
    }

    return success(data={
        "order_id": order_id,
        "pay_url": pay_url,
        "amount": amount,
        "amount_yuan": f"{amount/100:.2f}",
        "count": req.count,
        "pay_method": req.pay_method,
        "message": f"订单创建成功, 请使用{'微信' if req.pay_method == 'wechat' else '支付宝'}扫码支付 {amount/100:.2f} 元",
    })


@router.post("/pay/confirm", summary="支付确认 (模拟回调)", response_model=None)
@limiter.limit("20/minute")
async def pay_confirm(
    request: Request,
    req: PayConfirmRequest,
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """支付确认 - 模拟支付平台回调

    前端用户"完成支付"后调用此接口, 系统验证订单并激活 VIP / 增加额度
    """
    order = _pending_orders.get(req.order_id)
    if not order:
        return fail(BizError.RESOURCE_NOT_FOUND, "订单不存在或已过期")
    if order["user_id"] != current_user.id:
        return fail(BizError.ROLE_FORBIDDEN, "无权确认他人订单")
    if order["status"] != "pending":
        return fail(BizError.VALIDATION_ERROR, "订单已处理")

    # 刷新用户对象 (避免脏数据)
    db.refresh(current_user)

    try:
        if order["type"] == "vip_recharge":
            result = vip_service.activate_vip(current_user, db, order["plan"], pay_method=order.get("pay_method", "wechat"))
        elif order["type"] == "single_pay":
            result = vip_service.buy_single_quota(current_user, db, order["count"], pay_method=order.get("pay_method", "wechat"))
        else:
            return fail(BizError.VALIDATION_ERROR, "未知订单类型")

        # 标记订单完成
        order["status"] = "completed"
        order["completed_at"] = datetime.utcnow().isoformat()

        return success(data=result, message="支付成功, 权益已激活")
    except Exception as e:
        return fail(BizError.SYSTEM_ERROR, f"支付确认失败: {e}")


# ===== 管理员接口 =====
admin_router = APIRouter(prefix="/admin/vip", tags=["管理员-VIP管理"])


class AdminSetVipRequest(BaseModel):
    """管理员设置 VIP 请求"""
    user_id: int = Field(..., description="用户ID")
    is_vip: bool = Field(..., description="是否开通VIP")
    duration_days: int = Field(365, ge=1, le=3650, description="VIP时长(天)")


@admin_router.put("/set-vip", summary="管理员设置用户VIP状态", response_model=None)
async def admin_set_vip(
    req: AdminSetVipRequest,
    current_user: SysUser = Depends(require_role("ROLE_ADMIN")),
    db: Session = Depends(get_db),
):
    """管理员手动开通/取消用户 VIP"""
    try:
        result = vip_service.admin_set_vip(req.user_id, db, req.is_vip, req.duration_days, admin_id=current_user.id)
        return success(data=result, message=f"VIP 状态已{'开通' if req.is_vip else '取消'}")
    except ValueError as e:
        return fail(BizError.RESOURCE_NOT_FOUND, str(e))
    except Exception as e:
        return fail(BizError.SYSTEM_ERROR, f"操作失败: {e}")


@admin_router.get("/users", summary="获取用户VIP列表", response_model=None)
async def admin_vip_users(
    page: int = 1,
    size: int = 20,
    vip_only: bool = False,
    keyword: str = "",
    current_user: SysUser = Depends(require_role("ROLE_ADMIN")),
    db: Session = Depends(get_db),
):
    """管理员查看用户 VIP 状态列表"""
    from sqlalchemy import select, func
    conditions = [SysUser.role != "ROLE_ADMIN"]
    if vip_only:
        conditions.append(SysUser.is_vip == True)
    if keyword:
        conditions.append(
            (SysUser.username.contains(keyword))
            | (SysUser.nickname.contains(keyword))
        )

    count_stmt = select(func.count(SysUser.id)).where(*conditions)
    total = db.execute(count_stmt).scalar() or 0

    data_stmt = select(SysUser).where(*conditions)
    data_stmt = data_stmt.order_by(SysUser.is_vip.desc(), SysUser.created_at.desc())
    users = list(db.execute(data_stmt.offset((page - 1) * size).limit(size)).scalars())

    plan_label_map = {"monthly": "月卡", "quarterly": "季卡", "yearly": "年卡", "admin": "管理员开通"}

    items = [
        {
            "id": u.id,
            "username": u.username,
            "nickname": u.nickname,
            "role": u.role,
            "is_vip": u.is_vip,
            "vip_active": u.vip_active,
            "vip_plan_type": u.vip_plan_type,
            "vip_plan_label": plan_label_map.get(u.vip_plan_type, "") if u.vip_plan_type else "",
            "vip_expire_at": u.vip_expire_at.isoformat() if u.vip_expire_at else None,
            "free_quota_used": u.free_quota_used,
            "paid_quota": u.paid_quota,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
        for u in users
    ]
    return success(data={"items": items, "total": total, "page": page, "size": size})


@admin_router.get("/revenue", summary="平台营收统计", response_model=None)
async def admin_revenue(
    current_user: SysUser = Depends(require_role("ROLE_ADMIN")),
    db: Session = Depends(get_db),
):
    """管理员查看平台营收总览: 总收入、VIP数量、支付流水"""
    from sqlalchemy import func, select
    from app.models.payment import PaymentRecord

    type_map = {
        "vip_monthly": "VIP月卡",
        "vip_quarterly": "VIP季卡",
        "vip_yearly": "VIP年卡",
        "single_quota": "单次付费",
    }

    # 总收入 (分)
    total_revenue = db.execute(
        select(func.coalesce(func.sum(PaymentRecord.amount), 0))
        .where(PaymentRecord.status == "success")
    ).scalar() or 0

    # 按支付类型分组
    revenue_by_type = db.execute(
        select(PaymentRecord.pay_type, func.sum(PaymentRecord.amount), func.count(PaymentRecord.id))
        .where(PaymentRecord.status == "success")
        .group_by(PaymentRecord.pay_type)
    ).all()

    revenue_breakdown = [
        {
            "pay_type": row[0],
            "type_label": type_map.get(row[0], row[0]),
            "amount": row[1] or 0,
            "amount_yuan": f"{(row[1] or 0)/100:.2f}",
            "count": row[2],
        }
        for row in revenue_by_type
    ]

    # VIP 用户统计
    vip_count = db.execute(
        select(func.count(SysUser.id)).where(SysUser.is_vip == True)
    ).scalar() or 0

    # 按角色统计 VIP
    vip_by_role = db.execute(
        select(SysUser.role, func.count(SysUser.id))
        .where(SysUser.is_vip == True)
        .group_by(SysUser.role)
    ).all()

    role_map = {"ROLE_SEEKER": "求职者", "ROLE_EMPLOYER": "企业", "ROLE_ADMIN": "管理员"}
    vip_role_breakdown = [
        {"role": row[0], "role_label": role_map.get(row[0], row[0]), "count": row[1]}
        for row in vip_by_role
    ]

    # 按套餐类型统计 VIP 用户
    vip_by_plan = db.execute(
        select(SysUser.vip_plan_type, func.count(SysUser.id))
        .where(SysUser.is_vip == True, SysUser.vip_plan_type.isnot(None))
        .group_by(SysUser.vip_plan_type)
    ).all()

    plan_label_map = {"monthly": "月卡", "quarterly": "季卡", "yearly": "年卡", "admin": "管理员开通"}
    vip_plan_breakdown = [
        {"plan_type": row[0], "plan_label": plan_label_map.get(row[0], row[0]), "count": row[1]}
        for row in vip_by_plan
    ]

    # 近 30 天流水
    from datetime import datetime, timedelta
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_revenue = db.execute(
        select(func.coalesce(func.sum(PaymentRecord.amount), 0)).where(
            PaymentRecord.status == "success",
            PaymentRecord.created_at >= thirty_days_ago,
        )
    ).scalar() or 0

    # 最近 20 条支付记录
    recent_records = db.execute(
        select(PaymentRecord)
        .where(PaymentRecord.status == "success")
        .order_by(PaymentRecord.created_at.desc())
        .limit(20)
    ).scalars().all()

    recent_items = [
        {
            "id": r.id,
            "user_id": r.user_id,
            "username": r.user.username if r.user else "未知",
            "amount": r.amount,
            "amount_yuan": f"{r.amount/100:.2f}",
            "pay_type": r.pay_type,
            "type_label": type_map.get(r.pay_type, r.pay_type),
            "pay_method": r.pay_method,
            "detail": r.detail,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in recent_records
    ]

    return success(data={
        "total_revenue": total_revenue,
        "total_revenue_yuan": f"{total_revenue/100:.2f}",
        "recent_30_days": recent_revenue,
        "recent_30_days_yuan": f"{recent_revenue/100:.2f}",
        "revenue_breakdown": revenue_breakdown,
        "vip_count": vip_count,
        "vip_role_breakdown": vip_role_breakdown,
        "vip_plan_breakdown": vip_plan_breakdown,
        "recent_records": recent_items,
    })
