"""
SQLAlchemy 数据库基础设施
- Base: ORM 基类
- engine: 数据库引擎 (开发环境 GreatSQL/MySQL 8.0, 兼容 MySQL 协议)
- SessionLocal: 会话工厂
- get_db: FastAPI 依赖注入
"""
from typing import Generator

from sqlalchemy import BigInteger, Integer, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings


# 自增主键类型: SQLite 用 INTEGER PRIMARY KEY, MySQL 用 BIGINT AUTO_INCREMENT
BigIntPK = BigInteger().with_variant(Integer, "sqlite")


class Base(DeclarativeBase):
    """SQLAlchemy 2.0 声明式基类"""
    pass


def _create_engine():
    """根据数据库 URL 创建引擎, 兼容 SQLite 与 GreatSQL/MySQL"""
    url = settings.DATABASE_URL
    connect_args = {}
    pool_kwargs = {}
    if url.startswith("sqlite"):
        # SQLite 需要允许多线程访问 (FastAPI 多线程)
        connect_args["check_same_thread"] = False
    else:
        # MySQL/GreatSQL 连接池配置
        pool_kwargs = {"pool_size": 10, "max_overflow": 20, "pool_recycle": 3600}
    return create_engine(
        url,
        connect_args=connect_args,
        pool_pre_ping=True,
        echo=False,
        future=True,
        **pool_kwargs,
    )


engine = _create_engine()

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


def get_db() -> Generator:
    """FastAPI 依赖: 获取数据库会话, 请求结束自动关闭"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """创建所有表 (开发环境使用, 生产环境用 Alembic 迁移)"""
    # 导入所有模型以便 Base.metadata 注册
    from app.models import user, resume, job, skill, match, log, favorite  # noqa: F401

    Base.metadata.create_all(bind=engine)
