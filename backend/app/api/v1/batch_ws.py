"""
批量任务WebSocket - 实时推送批量执行进度
"""
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json

# 存储活跃的WebSocket连接，按task_id分组
batch_connections: Dict[str, Set[WebSocket]] = {}


async def batch_websocket_endpoint(websocket: WebSocket, task_id: str):
    """批量任务WebSocket端点

    Args:
        websocket: WebSocket连接
        task_id: 任务ID
    """
    await websocket.accept()

    # 添加到对应任务的连接集合
    if task_id not in batch_connections:
        batch_connections[task_id] = set()
    batch_connections[task_id].add(websocket)

    try:
        # 发送初始状态
        from app.services.batch_processor import batch_processor
        task = batch_processor.get_batch_task(task_id)
        if task:
            await websocket.send_json({
                "type": "init",
                "data": {
                    "task_id": task.task_id,
                    "status": task.status,
                    "progress": task.progress,
                    "current_step": task.current_step,
                    "total": task.total_cases,
                    "success": task.success,
                    "failed": task.failed,
                    "cases": [
                        {
                            "case_name": c.case_name,
                            "status": c.status,
                            "step1_output": c.step1_output,
                            "step2_output": c.step2_output,
                            "error": c.error
                        }
                        for c in task.cases
                    ]
                }
            })

        # 保持连接，接收客户端消息
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            # 处理客户端消息
            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        pass
    finally:
        # 移除连接
        if task_id in batch_connections:
            batch_connections[task_id].discard(websocket)
            if not batch_connections[task_id]:
                del batch_connections[task_id]


async def broadcast_batch_progress(task_id: str, task):
    """广播批量任务进度到所有订阅的客户端

    Args:
        task_id: 任务ID
        task: 任务对象
    """
    if task_id not in batch_connections:
        return

    data = {
        "type": "progress",
        "data": {
            "task_id": task.task_id,
            "status": task.status,
            "progress": task.progress,
            "current_step": task.current_step,
            "total": task.total_cases,
            "success": task.success,
            "failed": task.failed
        }
    }

    # 发送消息到所有连接的客户端
    disconnected = set()
    for connection in batch_connections[task_id]:
        try:
            await connection.send_json(data)
        except Exception:
            disconnected.add(connection)

    # 移除失效的连接
    for connection in disconnected:
        batch_connections[task_id].discard(connection)


async def broadcast_case_update(task_id: str, case_name: str, case_result):
    """广播单个case状态更新

    Args:
        task_id: 任务ID
        case_name: case名称
        case_result: case结果对象
    """
    if task_id not in batch_connections:
        return

    data = {
        "type": "case_update",
        "data": {
            "task_id": task_id,
            "case_name": case_name,
            "status": case_result.status,
            "step1_output": case_result.step1_output,
            "step2_output": case_result.step2_output,
            "error": case_result.error
        }
    }

    # 发送消息到所有连接的客户端
    disconnected = set()
    for connection in batch_connections[task_id]:
        try:
            await connection.send_json(data)
        except Exception:
            disconnected.add(connection)

    # 移除失效的连接
    for connection in disconnected:
        batch_connections[task_id].discard(connection)


async def broadcast_task_complete(task_id: str, task):
    """广播任务完成通知

    Args:
        task_id: 任务ID
        task: 任务对象
    """
    if task_id not in batch_connections:
        return

    data = {
        "type": "complete",
        "data": {
            "task_id": task.task_id,
            "status": task.status,
            "progress": 100,
            "total": task.total_cases,
            "success": task.success,
            "failed": task.failed,
            "cases": [
                {
                    "case_name": c.case_name,
                    "status": c.status,
                    "step1_output": c.step1_output,
                    "step2_output": c.step2_output,
                    "error": c.error
                }
                for c in task.cases
            ]
        }
    }

    # 发送消息到所有连接的客户端
    disconnected = set()
    for connection in batch_connections[task_id]:
        try:
            await connection.send_json(data)
        except Exception:
            disconnected.add(connection)

    # 移除失效的连接
    for connection in disconnected:
        batch_connections[task_id].discard(connection)
