"""
企业评价模型 - company_review 表
求职者面试结束后 (状态为"不合适"或"已录用") 对企业进行评分
"""
from datetime import datetime

from sqlalchemy import BigInteger, SmallInteger, Text, DateTime, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, BigIntPK


class CompanyReview(Base):
    """企业评价表 (按企业聚合, 每条评价关联一次投递/职位)"""

    __tablename__ = "company_review"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("sys_user.id"), nullable=False, comment="被评价企业用户ID")
    reviewer_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("sys_user.id"), nullable=False, comment="评价者(求职者)")
    job_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("job.id"), nullable=True, comment="关联职位")
    application_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("job_application.id"), nullable=True, comment="关联投递记录(防重复评价)")

    # 三维评分 (1-5)
    interview_score: Mapped[int] = mapped_column(SmallInteger, nullable=False, comment="面试体验 1-5")
    hr_score: Mapped[int] = mapped_column(SmallInteger, nullable=False, comment="HR响应速度 1-5")
    accuracy_score: Mapped[int] = mapped_column(SmallInteger, nullable=False, comment="职位描述准确度 1-5")
    comment: Mapped[str | None] = mapped_column(Text, nullable=True, comment="文字评价")

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # 关系 (仅查询用, 不修改既有模型)
    company = relationship("SysUser", foreign_keys=[company_id])
    reviewer = relationship("SysUser", foreign_keys=[reviewer_id])
    job = relationship("Job")

    __table_args__ = (
        Index("idx_review_company", "company_id"),
        Index("idx_review_reviewer", "reviewer_id"),
        Index("idx_review_application", "application_id"),
    )