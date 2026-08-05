"""
投递记录模型 - job_application 表
"""
from datetime import datetime

from sqlalchemy import (
    BigInteger, SmallInteger, Text, DateTime, ForeignKey, Index, UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, BigIntPK


class JobApplication(Base):
    """简历投递记录 (求职者向职位投递简历)"""

    __tablename__ = "job_application"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    resume_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("resume.id"), nullable=False)
    job_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("job.id"), nullable=False)
    applicant_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("sys_user.id"), nullable=False, comment="投递人(求职者)")
    # 状态: 0=已投递 1=已查看 2=面试邀请 3=不合适 4=已录用 5=已撤回
    status: Mapped[int] = mapped_column(SmallInteger, default=0, comment="0=已投递 1=已查看 2=面试邀请 3=不合适 4=已录用 5=已撤回")
    cover_letter: Mapped[str | None] = mapped_column(Text, nullable=True, comment="求职信")

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), comment="状态最后更新时间")

    # 关系 (不使用 back_populates, 避免修改已有模型)
    resume = relationship("Resume")
    job = relationship("Job")
    applicant = relationship("SysUser")

    __table_args__ = (
        Index("idx_app_applicant", "applicant_id"),
        Index("idx_app_job", "job_id"),
        Index("idx_app_resume", "resume_id"),
        UniqueConstraint("resume_id", "job_id", name="uq_app_resume_job"),
    )
