"""
职位收藏模型 - favorite 表
"""
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, BigIntPK


class Favorite(Base):
    """职位收藏表"""

    __tablename__ = "favorite"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("sys_user.id"), nullable=False)
    job_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("job.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "job_id", name="uk_user_job"),
        Index("idx_fav_user", "user_id"),
    )
