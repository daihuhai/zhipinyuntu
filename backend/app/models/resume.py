"""
简历模型 - resume 表 + resume_skill 关联表
"""
from datetime import datetime

from sqlalchemy import (
    BigInteger, String, Integer, SmallInteger, Text, LargeBinary,
    DateTime, ForeignKey, Float, Index, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, BigIntPK


class Resume(Base):
    """简历表 (一份简历对应一份 DOC/PDF 文档)"""

    __tablename__ = "resume"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("sys_user.id"), nullable=False)
    doc_url: Mapped[str] = mapped_column(String(256), nullable=False, comment="文档存储路径")
    doc_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="文档 MD5, 用于去重")

    # 解析状态: 0=待解析 1=解析中 2=成功 3=失败
    parse_status: Mapped[int] = mapped_column(SmallInteger, default=0)
    parse_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 结构化字段 (由豆包 AI 解析填充)
    name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    gender: Mapped[str | None] = mapped_column(String(8), nullable=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(128), nullable=True)
    current_city: Mapped[str | None] = mapped_column(String(32), nullable=True)
    intention_cities: Mapped[str | None] = mapped_column(String(256), nullable=True, comment="JSON 数组")
    education: Mapped[str | None] = mapped_column(String(16), nullable=True)
    school: Mapped[str | None] = mapped_column(String(64), nullable=True)
    major: Mapped[str | None] = mapped_column(String(64), nullable=True)
    work_years: Mapped[int | None] = mapped_column(Integer, nullable=True)
    expected_salary_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    expected_salary_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    self_evaluation: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 原始解析结果与向量
    raw_parse_json: Mapped[str | None] = mapped_column(Text, nullable=True, comment="完整解析 JSON")
    embedding: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True, comment="简历向量")

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # 关系
    user = relationship("SysUser", back_populates="resumes")
    skills = relationship("ResumeSkill", back_populates="resume", cascade="all, delete-orphan")
    match_records = relationship("MatchRecord", back_populates="resume", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_resume_user", "user_id"),
        Index("idx_resume_status", "parse_status"),
        Index("idx_resume_city", "current_city"),
    )


class ResumeSkill(Base):
    """简历技能关联表"""

    __tablename__ = "resume_skill"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    resume_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("resume.id"), nullable=False)
    skill_name: Mapped[str] = mapped_column(String(64), nullable=False)
    skill_level: Mapped[str | None] = mapped_column(String(16), nullable=True, comment="精通/熟练/掌握/了解")
    weight: Mapped[float] = mapped_column(Float, default=0.6)

    resume = relationship("Resume", back_populates="skills")

    __table_args__ = (
        Index("idx_rs_resume", "resume_id"),
        Index("idx_rs_skill", "skill_name"),
    )
