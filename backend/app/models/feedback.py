"""用户反馈模型"""
from datetime import datetime

from sqlalchemy import String, SmallInteger, Text, DateTime, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, BigIntPK


class Feedback(Base):
    """用户反馈表"""

    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("sys_user.id"), nullable=False, comment="提交用户ID")
    type: Mapped[str] = mapped_column(
        String(16), nullable=False, default="feature",
        comment="反馈类型: bug/feature/other"
    )
    title: Mapped[str] = mapped_column(String(128), nullable=False, comment="反馈标题")
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="反馈内容")
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="pending",
        comment="处理状态: pending/processing/resolved"
    )
    admin_reply: Mapped[str | None] = mapped_column(Text, nullable=True, comment="管理员回复")
    admin_id: Mapped[int | None] = mapped_column(ForeignKey("sys_user.id"), nullable=True, comment="处理管理员ID")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # 关系
    user = relationship("SysUser", foreign_keys=[user_id], backref="feedbacks")
    admin = relationship("SysUser", foreign_keys=[admin_id])