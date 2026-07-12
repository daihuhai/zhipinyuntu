"""面试邀请模型"""
from datetime import datetime
from sqlalchemy import BigInteger, SmallInteger, String, Text, DateTime, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, BigIntPK


class Interview(Base):
    __tablename__ = "interview"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    application_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("job_application.id"), nullable=False)
    employer_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("sys_user.id"), nullable=False)
    seeker_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("sys_user.id"), nullable=False)
    interview_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="面试时间")
    location: Mapped[str | None] = mapped_column(String(256), nullable=True, comment="面试地点")
    interview_type: Mapped[str] = mapped_column(String(32), default="线下", comment="面试形式: 线下/线上/电话")
    contact_person: Mapped[str | None] = mapped_column(String(64), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[int] = mapped_column(SmallInteger, default=0, comment="0=待确认 1=接受 2=拒绝")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    application = relationship("JobApplication")

    __table_args__ = (Index("idx_interview_app", "application_id"),)