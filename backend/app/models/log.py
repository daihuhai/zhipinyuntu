"""
操作日志模型 - admin_log 表
记录管理员操作、AI 大模型调用、数据导出等系统级操作
"""
from datetime import datetime

from sqlalchemy import BigInteger, String, Text, DateTime, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, BigIntPK


class AdminLog(Base):
    """系统操作日志 (含管理员操作 + AI 调用 + 数据导出)"""

    __tablename__ = "admin_log"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    # admin_id 可空: AI 大模型调用等系统操作没有管理员发起者
    admin_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("sys_user.id"), nullable=True)
    action: Mapped[str | None] = mapped_column(String(64), nullable=True)
    target_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    target_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip: Mapped[str | None] = mapped_column(String(64), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    admin = relationship("SysUser", back_populates="admin_logs")

    __table_args__ = (
        Index("idx_al_admin", "admin_id"),
        Index("idx_al_time", "created_at"),
        Index("idx_al_action", "action"),
    )
