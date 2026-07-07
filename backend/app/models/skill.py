"""
技能词典模型 - skill_dict 表
"""
from sqlalchemy import BigInteger, String, LargeBinary
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, BigIntPK


class SkillDict(Base):
    """技能词典 (统一技能名称, 用于归一化与向量检索)"""

    __tablename__ = "skill_dict"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    category: Mapped[str | None] = mapped_column(String(32), nullable=True, comment="编程语言/框架/工具/软技能")
    aliases: Mapped[str | None] = mapped_column(String(256), nullable=True, comment="别名 JSON 数组")
    embedding: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)

    def __repr__(self) -> str:
        return f"<SkillDict(name={self.name!r})>"
