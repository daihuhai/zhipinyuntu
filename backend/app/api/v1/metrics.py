"""性能监控指标接收"""
from fastapi import APIRouter, Request
from loguru import logger

router = APIRouter(prefix="/metrics", tags=["性能监控"])


@router.post("/web-vitals", summary="接收前端 Web Vitals 指标")
async def receive_web_vitals(request: Request):
    """接收前端上报的 Web Vitals 性能指标 (CLS/FCP/LCP/TTFB)"""
    try:
        body = await request.json()
        logger.info(f"Web Vitals: {body.get('name')}={body.get('value')} ({body.get('rating')}) on {body.get('page')}")
    except Exception:
        pass
    return {"code": 0, "message": "ok"}