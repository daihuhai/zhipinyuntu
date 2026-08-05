"""
用户模型 - sys_user 表
统一存储个人/企业/管理员用户,企业字段与个人字段并列 (按 role 区分填写)
"""
from datetime import datetime, date

from sqlalchemy import BigInteger, String, SmallInteger, DateTime, func, Index, Boolean, Text, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, BigIntPK


class SysUser(Base):
    """系统用户表 (个人 ROLE_SEEKER / 企业 ROLE_EMPLOYER / 管理员 ROLE_ADMIN)"""

    __tablename__ = "sys_user"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(128), nullable=False, comment="BCrypt 哈希")
    role: Mapped[str] = mapped_column(String(16), nullable=False, comment="ROLE_SEEKER/ROLE_EMPLOYER/ROLE_ADMIN")
    phone: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True)
    email: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True)
    nickname: Mapped[str | None] = mapped_column(String(64), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(256), nullable=True)

    # 企业用户字段
    company_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    credit_code: Mapped[str | None] = mapped_column(String(32), nullable=True, comment="统一社会信用代码")
    contact_person: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # 个人用户字段
    real_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    gender: Mapped[str | None] = mapped_column(String(8), nullable=True)
    id_card: Mapped[str | None] = mapped_column(String(18), nullable=True, comment="身份证号")
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True, comment="出生日期")
    education: Mapped[str | None] = mapped_column(String(32), nullable=True, comment="最高学历")
    work_years: Mapped[int | None] = mapped_column(SmallInteger, nullable=True, comment="工作年限")

    # VIP 制度字段
    is_vip: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否VIP用户")
    vip_plan_type: Mapped[str | None] = mapped_column(String(16), nullable=True, comment="VIP套餐类型: monthly/quarterly/yearly/admin")
    vip_expire_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="VIP到期时间")
    free_quota_used: Mapped[int] = mapped_column(SmallInteger, default=0, comment="免费配额已用次数")
    paid_quota: Mapped[int] = mapped_column(SmallInteger, default=0, comment="单次付费购买次数")

    # 状态
    status: Mapped[int] = mapped_column(SmallInteger, default=1, comment="0=禁用 1=启用")
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    # 新用户引导: 0=未完成(需展示引导) 1=已完成(不再展示)
    onboard_done: Mapped[int] = mapped_column(SmallInteger, default=0, comment="0=引导未完成 1=引导已完成")

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # 关系
    resumes = relationship("Resume", back_populates="user", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="user", cascade="all, delete-orphan")
    admin_logs = relationship("AdminLog", back_populates="admin", cascade="all, delete-orphan")
    payment_records = relationship("PaymentRecord", back_populates="user", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_user_role", "role"),
        Index("idx_user_status", "status"),
        Index("idx_user_vip", "is_vip"),
    )

    @property
    def vip_active(self) -> bool:
        """VIP 是否生效 (含过期判断)"""
        if not self.is_vip:
            return False
        if self.vip_expire_at:
            from datetime import datetime as _dt
            if _dt.utcnow() > self.vip_expire_at:
                return False
        return True

    def __repr__(self) -> str:
        return f"<SysUser(id={self.id}, username={self.username!r}, role={self.role}, vip={self.is_vip})>"
