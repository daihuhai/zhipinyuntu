"""
支付流水模型 - payment_record 表
追踪所有 VIP 充值、单次购买的支付记录
"""
from datetime import datetime

from sqlalchemy import BigInteger, String, Integer, DateTime, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, BigIntPK


class PaymentRecord(Base):
    """支付流水记录"""

    __tablename__ = "payment_record"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("sys_user.id"), nullable=False, comment="用户ID")
    amount: Mapped[int] = mapped_column(Integer, default=0, comment="金额(分), 如 2900 表示 29.00 元")
    pay_type: Mapped[str] = mapped_column(String(32), nullable=False, comment="类型: vip_monthly/vip_quarterly/vip_yearly/single_quota")
    pay_method: Mapped[str] = mapped_column(String(16), nullable=False, comment="支付方式: wechat/alipay")
    status: Mapped[str] = mapped_column(String(16), default="success", comment="状态: pending/success/refund")
    detail: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="详情描述")

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="支付时间")

    user = relationship("SysUser", back_populates="payment_records")

    __table_args__ = (
        Index("idx_pr_user", "user_id"),
        Index("idx_pr_time", "created_at"),
        Index("idx_pr_type", "pay_type"),
    )