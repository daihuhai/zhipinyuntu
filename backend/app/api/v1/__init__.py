"""API v1 路由聚合"""
from fastapi import APIRouter

from app.api.v1.health import router as health_router
from app.api.v1.auth import router as auth_router
from app.api.v1.resume import router as resume_router
from app.api.v1.job import router as job_router
from app.api.v1.graph import router as graph_router
from app.api.v1.match import router as match_router
from app.api.v1.application import router as application_router
from app.api.v1.admin import router as admin_router
from app.api.v1.message import router as message_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(resume_router)
api_router.include_router(job_router)
api_router.include_router(graph_router)
api_router.include_router(match_router)
api_router.include_router(application_router)
api_router.include_router(admin_router)
api_router.include_router(message_router)

__all__ = ["api_router"]
