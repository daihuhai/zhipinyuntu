"""
职位模型 - job 表 + job_requirement 表
"""
from datetime import datetime

from sqlalchemy import (
    BigInteger, String, Integer, SmallInteger, Text, LargeBinary,
    DateTime, ForeignKey, Float, Index, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, BigIntPK


class Job(Base):
    """职位表"""

    __tablename__ = "job"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("sys_user.id"), nullable=False)
    doc_url: Mapped[str | None] = mapped_column(String(256), nullable=True, comment="职位描述文档(可选)")

    title: Mapped[str] = mapped_column(String(128), nullable=False)
    company: Mapped[str | None] = mapped_column(String(128), nullable=True)
    department: Mapped[str | None] = mapped_column(String(64), nullable=True)
    job_type: Mapped[str | None] = mapped_column(String(16), nullable=True, comment="全职/兼职/实习")
    salary_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_unit: Mapped[str | None] = mapped_column(String(8), nullable=True, default="K")
    work_city: Mapped[str | None] = mapped_column(String(32), nullable=True)
    experience_required: Mapped[str | None] = mapped_column(String(32), nullable=True)
    education_required: Mapped[str | None] = mapped_column(String(16), nullable=True)
    headcount: Mapped[int] = mapped_column(Integer, default=1)

    # 状态: 0=下架 1=招聘中 2=草稿
    status: Mapped[int] = mapped_column(SmallInteger, default=1)
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="职位详细描述")

    raw_parse_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    embedding: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # 关系
    user = relationship("SysUser", back_populates="jobs")
    requirements = relationship("JobRequirement", back_populates="job", cascade="all, delete-orphan")
    match_records = relationship("MatchRecord", back_populates="job", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_job_user", "user_id"),
        Index("idx_job_city", "work_city"),
        Index("idx_job_status", "status"),
    )


class JobRequirement(Base):
    """职位要求表 (技能要求)"""

    __tablename__ = "job_requirement"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("job.id"), nullable=False)
    skill_name: Mapped[str] = mapped_column(String(64), nullable=False)
    skill_level: Mapped[str | None] = mapped_column(String(16), nullable=True)
    req_type: Mapped[str | None] = mapped_column(String(8), nullable=True, comment="必须/优先")
    weight: Mapped[float] = mapped_column(Float, default=1.0)

    job = relationship("Job", back_populates="requirements")

    __table_args__ = (
        Index("idx_jr_job", "job_id"),
        Index("idx_jr_skill", "skill_name"),
    )
