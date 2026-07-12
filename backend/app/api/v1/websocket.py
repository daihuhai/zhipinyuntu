"""WebSocket 消息推送 (实时通知)"""
import json
import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from loguru import logger

from app.core.security import decode_token

router = APIRouter()

# 连接池: user_id -> [websocket1, websocket2, ...]
connections: dict[int, list[WebSocket]] = {}


@router.websocket("/ws/messages")
async def ws_messages(websocket: WebSocket, token: str = Query(...)):
    """WebSocket 消息推送端点
    前端连接: ws://localhost:8000/api/v1/ws/messages?token=xxx
    """
    try:
        payload = decode_token(token)
        user_id = payload.get("user_id")
        if not user_id:
            await websocket.close(code=4001, reason="Invalid token")
            return
    except Exception:
        await websocket.close(code=4001, reason="Invalid token")
        return

    await websocket.accept()
    user_id = int(user_id)

    # 注册连接
    if user_id not in connections:
        connections[user_id] = []
    connections[user_id].append(websocket)
    logger.info(f"WebSocket 连接: user_id={user_id}, 当前连接数={len(connections[user_id])}")

    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        # 清理连接
        if user_id in connections:
            connections[user_id].remove(websocket)
            if not connections[user_id]:
                del connections[user_id]
            logger.info(f"WebSocket 断开: user_id={user_id}")


def notify_user(user_id: int, message: dict) -> None:
    """向指定用户推送消息 (同步调用, 可在任意线程中使用)"""
    if user_id not in connections:
        return
    dead = []
    for ws in connections[user_id]:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(ws.send_text(json.dumps(message, ensure_ascii=False)))
            else:
                loop.run_until_complete(ws.send_text(json.dumps(message, ensure_ascii=False)))
        except Exception:
            dead.append(ws)
    for ws in dead:
        if user_id in connections:
            connections[user_id].remove(ws)
    if user_id in connections and not connections[user_id]:
        del connections[user_id]