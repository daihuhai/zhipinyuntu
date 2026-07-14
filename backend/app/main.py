"""
智聘云图 - FastAPI 应用入口
基于文档智能解析的人岗匹配平台
"""
import logging
import secrets
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.limiter import limiter
from app.api.v1 import api_router


# ===== 日志配置 =====
logger.remove()
logger.add(
    logging.StreamHandler(),
    level="DEBUG" if settings.APP_DEBUG else "INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | "
           "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} 启动中...")
    logger.info(f"   运行环境: {settings.APP_ENV}")
    logger.info(f"   灵犀大模型: {settings.ARK_CHAT_MODEL}")

    # 初始化数据库 (开发环境: 自动建表 + 默认管理员)
    from app.db.base import init_db, SessionLocal
    from app.models.user import SysUser
    from app.core.security import hash_password
    init_db()
    logger.info("✅ 数据库表已就绪")

    # 创建默认管理员账号 (仅当不存在时, 使用随机强密码)
    with SessionLocal() as db:
        from sqlalchemy import select
        admin = db.execute(
            select(SysUser).where(SysUser.role == "ROLE_ADMIN")
        ).scalar_one_or_none()
        if admin is None:
            # 生成随机强密码 (12 位, 字母+数字)
            admin_password = secrets.token_urlsafe(9)[:12]
            admin = SysUser(
                username="admin",
                password_hash=hash_password(admin_password),
                role="ROLE_ADMIN",
                nickname="系统管理员",
                status=1,
            )
            db.add(admin)
            db.commit()
            logger.info("✅ 默认管理员已创建")
            logger.info(f"   账号: admin")
            logger.info(f"   密码: {admin_password}")
            logger.info(f"   ⚠️  请立即修改密码并妥善保存, 此密码仅显示一次")
        else:
            logger.info("✅ 管理员账号已存在")

    logger.info(f"✅ {settings.APP_NAME} 启动完成, 监听 {settings.BACKEND_HOST}:{settings.BACKEND_PORT}")
    yield
    logger.info(f"👋 {settings.APP_NAME} 关闭中...")


# ===== 创建 FastAPI 应用 =====
app = FastAPI(
    title=settings.APP_NAME,
    description="基于文档智能解析的人岗匹配平台 - B/S 架构",
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.APP_DEBUG else None,
    redoc_url="/redoc" if settings.APP_DEBUG else None,
    openapi_url="/openapi.json" if settings.APP_DEBUG else None,
    lifespan=lifespan,
)

# ===== 速率限制异常处理 =====
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ===== CORS 中间件 (收紧: 仅允许必要方法和头部) =====
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "X-Trace-Id", "X-Requested-With"],
)


# ===== 统一响应中间件 =====
@app.middleware("http")
async def unified_response_middleware(request: Request, call_next):
    """统一 JSON 响应为 {code, message, data, trace_id} 格式"""
    import uuid
    response = await call_next(request)
    trace_id = request.headers.get("X-Trace-Id", str(uuid.uuid4()))
    response.headers["X-Trace-Id"] = trace_id
    return response


# ===== 全局异常处理 =====
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"未处理异常: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "code": 5000,
            "message": "系统内部错误",
            "data": None,
            "trace_id": request.headers.get("X-Trace-Id", ""),
        },
    )


# ===== 注册路由 =====
app.include_router(api_router)

# ===== 挂载静态文件 (上传的文档) =====
import os as _os
_uploads_dir = _os.path.abspath(settings.STORAGE_PATH)
_os.makedirs(_uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=_uploads_dir), name="uploads")


# ===== 根路径 =====
@app.get("/", tags=["根路径"], summary="服务信息")
async def root():
    """根路径, 返回服务基本信息"""
    return {
        "code": 0,
        "message": "success",
        "data": {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "env": settings.APP_ENV,
            "docs": "/docs",
            "health": "/api/v1/health",
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=settings.APP_DEBUG,
        log_level="debug" if settings.APP_DEBUG else "info",
    )
