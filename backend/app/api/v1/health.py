"""健康检查接口 - 用于 M1 基础设施验证"""
import time
from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["健康检查"])

# 服务启动时间
START_TIME = time.time()


@router.get("", summary="健康检查")
async def health_check():
    """基础健康检查, 验证服务是否存活"""
    return {
        "status": "ok",
        "service": "智聘云图",
        "version": "1.0.0",
        "uptime_seconds": round(time.time() - START_TIME, 2),
    }


@router.get("/detail", summary="详细健康检查")
async def health_check_detail():
    """详细健康检查, 包含各组件连通性"""
    from app.core.config import settings

    checks = {
        "api": "ok",
        "database": "skipped",  # M2 接入
        "redis": "skipped",     # M2 接入
        "neo4j": "skipped",     # M3 接入
        "ark_api": "configured" if settings.ARK_API_KEY else "missing",
    }

    all_ok = all(v in ("ok", "skipped", "configured") for v in checks.values())
    return {
        "status": "ok" if all_ok else "degraded",
        "checks": checks,
        "env": settings.APP_ENV,
    }
