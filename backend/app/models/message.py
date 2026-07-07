"""
消息模型 - message 表
求职者与企业之间的消息系统
"""
from datetime import datetime

from sqlalchemy import (
    BigInteger, String, SmallInteger, Text,
    DateTime, ForeignKey, func, Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, BigIntPK


class Message(Base):
    """消息表"""

    __tablename__ = "message"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    sender_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("sys_user.id"), nullable=False)
    receiver_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("sys_user.id"), nullable=False)
    job_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("job.id"), nullable=True, comment="关联职位(可选)")
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[int] = mapped_column(SmallInteger, default=0, comment="0=未读 1=已读")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    sender = relationship("SysUser", foreign_keys=[sender_id])
    receiver = relationship("SysUser", foreign_keys=[receiver_id])

    __table_args__ = (
        Index("idx_msg_sender", "sender_id"),
        Index("idx_msg_receiver", "receiver_id"),
        Index("idx_msg_read", "is_read"),
    )
