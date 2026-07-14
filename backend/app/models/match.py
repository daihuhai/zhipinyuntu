"""
匹配记录模型 - match_record 表
"""
from datetime import datetime

from sqlalchemy import BigInteger, String, Float, Text, DateTime, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, BigIntPK


class MatchRecord(Base):
    """人岗匹配记录 (含各维度评分 + 灵犀生成的匹配依据)"""

    __tablename__ = "match_record"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    resume_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("resume.id"), nullable=False)
    job_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("job.id"), nullable=False)

    total_score: Mapped[float] = mapped_column(Float, nullable=False)
    skill_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    exp_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    edu_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    city_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    proj_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    salary_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    semantic_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    match_reason: Mapped[str | None] = mapped_column(Text, nullable=True, comment="灵犀模型生成的自然语言依据")
    direction: Mapped[str | None] = mapped_column(String(16), nullable=True, comment="JOB_TO_RESUME/RESUME_TO_JOB")

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # 关系
    resume = relationship("Resume", back_populates="match_records")
    job = relationship("Job", back_populates="match_records")

    __table_args__ = (
        Index("idx_mr_resume", "resume_id", "total_score"),
        Index("idx_mr_job", "job_id", "total_score"),
    )
