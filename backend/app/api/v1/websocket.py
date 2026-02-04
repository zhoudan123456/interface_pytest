"""
WebSocket API - 实时推送任务进度
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
from typing import Set

router = APIRouter()

# 存储活跃的WebSocket连接
active_connections: Set[WebSocket] = set()


@router.websocket("/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    """WebSocket端点 - 实时推送任务进度

    Args:
        websocket: WebSocket连接
        task_id: 任务ID
    """
    await websocket.accept()
    active_connections.add(websocket)

    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_text()
            message = json.loads(data)

            # 处理不同类型的消息
            if message.get("type") == "subscribe":
                # 订阅任务进度推送
                from app.models.task import get_task

                task = get_task(task_id)
                if task:
                    await websocket.send_json({
                        "type": "progress",
                        "data": {
                            "progress": task.progress,
                            "message": task.current_step or "",
                            "status": task.status
                        }
                    })
            elif message.get("type") == "unsubscribe":
                # 取消订阅
                break

    except WebSocketDisconnect:
        pass
    finally:
        active_connections.remove(websocket)


async def broadcast_task_progress(task_id: str, progress: int, message: str, status: str):
    """广播任务进度到所有订阅的客户端

    Args:
        task_id: 任务ID
        progress: 进度百分比
        message: 进度消息
        status: 任务状态
    """
    if not active_connections:
        return

    data = {
        "type": "progress",
        "data": {
            "task_id": task_id,
            "progress": progress,
            "message": message,
            "status": status
        }
    }

    # 发送消息到所有连接的客户端
    for connection in active_connections:
        try:
            await connection.send_json(data)
        except:
            # 移除失效的连接
            active_connections.discard(connection)
