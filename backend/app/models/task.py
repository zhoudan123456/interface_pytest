"""
任务数据模型
"""
from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
import uuid

class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskCreate(BaseModel):
    """创建任务请求"""
    excel_file_id: str = Field(..., description="Excel文件ID")
    json_file_id: str = Field(..., description="JSON文件ID")


class TaskResponse(BaseModel):
    """任务响应"""
    task_id: str = Field(..., description="任务ID")
    status: TaskStatus = Field(..., description="任务状态")
    progress: int = Field(default=0, ge=0, le=100, description="进度百分比")
    current_step: Optional[str] = Field(None, description="当前步骤描述")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    result: Optional[Dict[str, Any]] = Field(None, description="任务结果")
    error: Optional[str] = Field(None, description="错误信息")


class TaskInDB(TaskResponse):
    """数据库中的任务"""
    excel_path: str
    json_path: str


# 内存存储（生产环境应使用Redis或数据库）
tasks_db: Dict[str, TaskInDB] = {}


def create_task(excel_file_id: str, json_file_id: str, excel_path: str, json_path: str) -> TaskInDB:
    """创建新任务"""
    task_id = str(uuid.uuid4())
    task = TaskInDB(
        task_id=task_id,
        status=TaskStatus.PENDING,
        progress=0,
        excel_path=excel_path,
        json_path=json_path,
        created_at=datetime.now()
    )
    tasks_db[task_id] = task
    return task


def get_task(task_id: str) -> Optional[TaskInDB]:
    """获取任务"""
    return tasks_db.get(task_id)


def update_task(task_id: str, **kwargs) -> Optional[TaskInDB]:
    """更新任务"""
    task = tasks_db.get(task_id)
    if not task:
        return None

    for key, value in kwargs.items():
        if hasattr(task, key):
            setattr(task, key, value)

    task.updated_at = datetime.now()
    return task
