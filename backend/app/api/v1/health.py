"""健康检查接口 - 服务存活检测"""
import time
from datetime import datetime, timezone

from fastapi import APIRouter
from sqlalchemy import text

from app.core.config import settings
from app.db.base import engine

router = APIRouter(prefix="/health", tags=["健康检查"])

START_TIME = time.time()


@router.get("", summary="轻量级健康检查")
async def health_check():
    """基础健康检查, 验证服务是否存活 + 数据库连通性"""
    db_ok = True
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        db_ok = False

    return {
        "code": 0,
        "message": "success",
        "data": {
            "status": "ok" if db_ok else "degraded",
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "env": settings.APP_ENV,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "uptime_seconds": round(time.time() - START_TIME, 2),
            "database": "ok" if db_ok else "error",
        },
    }
