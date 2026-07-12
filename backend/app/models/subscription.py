"""职位订阅模型"""
from datetime import datetime
from sqlalchemy import BigInteger, SmallInteger, String, DateTime, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, BigIntPK


class JobSubscription(Base):
    __tablename__ = "job_subscription"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("sys_user.id"), nullable=False)
    cities: Mapped[str | None] = mapped_column(String(256), nullable=True, comment="意向城市(逗号分隔)")
    job_types: Mapped[str | None] = mapped_column(String(256), nullable=True, comment="意向职位类型(逗号分隔)")
    keywords: Mapped[str | None] = mapped_column(String(256), nullable=True, comment="关键词")
    enabled: Mapped[int] = mapped_column(SmallInteger, default=1, comment="0=关闭 1=开启")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user = relationship("SysUser")

    __table_args__ = (Index("idx_sub_user", "user_id"),)