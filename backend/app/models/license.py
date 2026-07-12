"""企业资质认证模型"""
from datetime import datetime
from sqlalchemy import BigInteger, SmallInteger, String, DateTime, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, BigIntPK


class BusinessLicense(Base):
    __tablename__ = "business_license"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("sys_user.id"), nullable=False, unique=True)
    company_name: Mapped[str] = mapped_column(String(128), nullable=False)
    credit_code: Mapped[str] = mapped_column(String(64), nullable=False)
    license_image: Mapped[str] = mapped_column(String(256), nullable=False, comment="营业执照图片URL")
    status: Mapped[int] = mapped_column(SmallInteger, default=0, comment="0=待审核 1=通过 2=拒绝")
    audit_remark: Mapped[str | None] = mapped_column(String(256), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user = relationship("SysUser")

    __table_args__ = (Index("idx_license_user", "user_id"),)