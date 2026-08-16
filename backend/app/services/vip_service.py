"""
VIP 配额服务
- 免费配额: 求职者 2 次 / 企业 3 次 (简历解析 + 智能匹配共用)
- VIP 用户: 无限次
- 求职者: 单次 0.5 元, 月卡 29 / 季卡 79 / 年卡 299
- 企业: 单次 2 元, 月卡 99 / 季卡 269 / 年卡 899
"""
from datetime import datetime, timedelta
from typing import Literal

from sqlalchemy.orm import Session
from loguru import logger

from app.models.user import SysUser

# 免费配额上限 (按角色区分)
FREE_QUOTA_LIMITS = {
    "ROLE_SEEKER": 2,
    "ROLE_EMPLOYER": 3,
    "ROLE_ADMIN": 999,
}
# 默认免费配额 (兜底)
FREE_QUOTA_LIMIT = 2

# VIP 套餐配置 - 求职者 (价格单位: 分)
VIP_PLANS_SEEKER = {
    "monthly": {"name": "月卡 VIP", "price": 2900, "duration_days": 30, "desc": "30 天无限次灵犀解析与匹配"},
    "quarterly": {"name": "季卡 VIP", "price": 7900, "duration_days": 90, "desc": "90 天无限次灵犀解析与匹配, 省 8 元"},
    "yearly": {"name": "年卡 VIP", "price": 29900, "duration_days": 365, "desc": "365 天无限次灵犀解析与匹配, 省 49 元"},
}

# VIP 套餐配置 - 企业 (价格更贵)
VIP_PLANS_EMPLOYER = {
    "monthly": {"name": "月卡 VIP", "price": 9900, "duration_days": 30, "desc": "30 天无限次灵犀解析与匹配"},
    "quarterly": {"name": "季卡 VIP", "price": 26900, "duration_days": 90, "desc": "90 天无限次灵犀解析与匹配, 省 28 元"},
    "yearly": {"name": "年卡 VIP", "price": 89900, "duration_days": 365, "desc": "365 天无限次灵犀解析与匹配, 省 188 元"},
}

# 兼容: 默认使用求职者套餐 (外部直接引用 VIP_PLANS 的地方)
VIP_PLANS = VIP_PLANS_SEEKER

# 单次付费 (单位: 分)
SINGLE_PAY_PRICE_SEEKER = 50   # 0.5 元
SINGLE_PAY_PRICE_EMPLOYER = 200  # 2 元
SINGLE_PAY_PRICE = 50  # 兼容默认


def get_vip_plans(role: str) -> dict:
    """根据角色获取 VIP 套餐配置"""
    if role == "ROLE_EMPLOYER":
        return VIP_PLANS_EMPLOYER
    return VIP_PLANS_SEEKER


def get_free_quota_limit(role: str) -> int:
    """根据角色获取免费配额上限"""
    return FREE_QUOTA_LIMITS.get(role, FREE_QUOTA_LIMIT)


def get_single_pay_price(role: str) -> int:
    """根据角色获取单次付费价格 (分)"""
    if role == "ROLE_EMPLOYER":
        return SINGLE_PAY_PRICE_EMPLOYER
    return SINGLE_PAY_PRICE_SEEKER


class QuotaExceededException(Exception):
    """配额不足异常"""

    def __init__(self, message: str, quota_info: dict):
        self.message = message
        self.quota_info = quota_info
        super().__init__(message)


class VipService:
    """VIP 配额管理服务"""

    def get_quota_info(self, user: SysUser) -> dict:
        """获取用户配额信息"""
        is_vip = user.vip_active
        free_limit = get_free_quota_limit(user.role)
        remaining = 0 if is_vip else max(0, free_limit - user.free_quota_used)

        # 计算剩余天数
        remaining_days = 0
        if is_vip and user.vip_expire_at:
            delta = user.vip_expire_at - datetime.utcnow()
            remaining_days = max(0, delta.days)

        return {
            "is_vip": is_vip,
            "vip_plan_type": user.vip_plan_type,
            "vip_expire_at": user.vip_expire_at.isoformat() if user.vip_expire_at else None,
            "vip_remaining_days": remaining_days,
            "free_quota_limit": free_limit,
            "free_quota_used": user.free_quota_used,
            "free_quota_remaining": remaining,
            "paid_quota": user.paid_quota,
            "total_remaining": "无限" if is_vip else remaining + user.paid_quota,
        }

    def check_and_consume_quota(self, user: SysUser, db: Session, action: str = "ai_operation") -> None:
        """检查并消耗一次配额

        优先级: VIP(无限) > 单次付费额度 > 免费配额
        若全部用尽, 抛出 QuotaExceededException
        """
        # VIP 用户: 无限次
        if user.vip_active:
            logger.info(f"用户 {user.id} VIP 用户, 无限配额, 操作: {action}")
            return

        # 单次付费额度
        if user.paid_quota > 0:
            user.paid_quota -= 1
            db.commit()
            logger.info(f"用户 {user.id} 消耗单次付费额度, 剩余 {user.paid_quota}, 操作: {action}")
            return

        # 免费配额 (按角色区分上限)
        free_limit = get_free_quota_limit(user.role)
        if user.free_quota_used < free_limit:
            user.free_quota_used += 1
            db.commit()
            remaining = free_limit - user.free_quota_used
            logger.info(f"用户 {user.id} 消耗免费配额, 已用 {user.free_quota_used}/{free_limit}, 操作: {action}")
            return

        # 配额用尽
        raise QuotaExceededException(
            "免费配额已用尽, 请升级 VIP 或购买单次解析",
            self.get_quota_info(user),
        )

    def activate_vip(self, user: SysUser, db: Session, plan: str, pay_method: str = "wechat") -> dict:
        """激活 VIP (充值成功后调用)

        Args:
            plan: monthly/quarterly/yearly
            pay_method: wechat/alipay
        Returns:
            VIP 信息
        """
        vip_plans = get_vip_plans(user.role)
        if plan not in vip_plans:
            raise ValueError(f"无效的 VIP 套餐: {plan}")

        plan_info = vip_plans[plan]
        now = datetime.utcnow()

        # 如果已是 VIP 且未过期, 在原到期时间基础上延长
        if user.vip_active and user.vip_expire_at:
            base = user.vip_expire_at
        else:
            base = now

        user.vip_expire_at = base + timedelta(days=plan_info["duration_days"])
        user.is_vip = True
        user.vip_plan_type = plan
        db.commit()
        db.refresh(user)

        logger.info(f"用户 {user.id} 激活 VIP {plan}, 到期时间: {user.vip_expire_at}")

        # 写入支付流水
        try:
            from app.models.payment import PaymentRecord
            pay_type_map = {"monthly": "vip_monthly", "quarterly": "vip_quarterly", "yearly": "vip_yearly"}
            record = PaymentRecord(
                user_id=user.id,
                amount=plan_info["price"],
                pay_type=pay_type_map.get(plan, "vip_monthly"),
                pay_method=pay_method,
                status="success",
                detail=f"充值 {plan_info['name']}",
            )
            db.add(record)
            db.commit()
        except Exception:
            pass

        # 记录操作日志
        try:
            from app.services.admin_service import admin_service
            admin_service.write_system_log(
                db,
                action="VIP_RECHARGE",
                target_type="user",
                target_id=user.id,
                detail=f"用户充值 VIP {plan_info['name']}, 价格 {plan_info['price']/100:.2f} 元",
            )
        except Exception:
            pass

        return self.get_quota_info(user)

    def buy_single_quota(self, user: SysUser, db: Session, count: int = 1, pay_method: str = "wechat") -> dict:
        """购买单次付费额度

        Args:
            count: 购买次数 (默认 1 次)
            pay_method: wechat/alipay
        Returns:
            配额信息
        """
        single_price = get_single_pay_price(user.role)
        user.paid_quota += count
        db.commit()

        logger.info(f"用户 {user.id} 购买单次配额 {count} 次, 总计 {user.paid_quota} 次")

        # 写入支付流水
        try:
            from app.models.payment import PaymentRecord
            record = PaymentRecord(
                user_id=user.id,
                amount=single_price * count,
                pay_type="single_quota",
                pay_method=pay_method,
                status="success",
                detail=f"购买单次解析 {count} 次",
            )
            db.add(record)
            db.commit()
        except Exception:
            pass

        # 记录操作日志
        try:
            from app.services.admin_service import admin_service
            admin_service.write_system_log(
                db,
                action="SINGLE_PAY_PURCHASE",
                target_type="user",
                target_id=user.id,
                detail=f"用户购买单次配额 {count} 次, 价格 {count * single_price / 100:.2f} 元",
            )
        except Exception:
            pass

        return self.get_quota_info(user)

    def admin_set_vip(self, user_id: int, db: Session, is_vip: bool, duration_days: int = 365, admin_id: int | None = None) -> dict:
        """管理员设置用户 VIP 状态"""
        user = db.get(SysUser, user_id)
        if not user:
            raise ValueError("用户不存在")

        # 根据天数映射套餐类型
        plan_map = {30: "monthly", 90: "quarterly", 365: "yearly"}
        plan_type = plan_map.get(duration_days, "admin")

        if is_vip:
            now = datetime.utcnow()
            if user.vip_active and user.vip_expire_at:
                user.vip_expire_at = user.vip_expire_at + timedelta(days=duration_days)
            else:
                user.vip_expire_at = now + timedelta(days=duration_days)
            user.is_vip = True
            user.vip_plan_type = plan_type
        else:
            user.is_vip = False
            user.vip_expire_at = None
            user.vip_plan_type = None

        db.commit()
        db.refresh(user)

        # 记录操作日志
        try:
            from app.services.admin_service import admin_service
            plan_label = {"monthly": "月卡", "quarterly": "季卡", "yearly": "年卡", "admin": "管理员开通"}.get(plan_type, plan_type)
            admin_service.write_log(
                db,
                admin_id=admin_id,
                action="ADMIN_SET_VIP",
                target_type="user",
                target_id=user_id,
                detail=f"管理员设置用户 VIP 状态: {'开通' if is_vip else '取消'} {plan_label} ({duration_days}天)",
            )
        except Exception:
            pass

        return self.get_quota_info(user)


vip_service = VipService()
