"""
批量处理相关数据模型
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class CaseResult(BaseModel):
    """单个case的处理结果"""
    case_name: str
    status: str = Field(default="pending", description="pending | processing | success | failed")
    step1_output: Optional[str] = Field(default=None, description="步骤1输出文件名")
    step2_output: Optional[str] = Field(default=None, description="步骤2输出文件名")
    error: Optional[str] = Field(default=None, description="错误信息")
    start_time: Optional[datetime] = Field(default=None, description="开始时间")
    end_time: Optional[datetime] = Field(default=None, description="结束时间")

    class Config:
        json_schema_extra = {
            "example": {
                "case_name": "case_001",
                "status": "success",
                "step1_output": "case_001_check_point_20260204_100015.json",
                "step2_output": "case_001_validation_report_20260204_100022.md",
                "error": None
            }
        }


class DatasetInfo(BaseModel):
    """数据集信息"""
    name: str
    case_count: int
    created_at: datetime
    size_mb: float
    cases: List[str] = Field(default_factory=list, description="case名称列表")
    path: str = Field(default="", description="数据集路径")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "dataset_001",
                "case_count": 10,
                "created_at": "2026-02-04T10:00:00",
                "size_mb": 125.5,
                "cases": ["case_001", "case_002", "case_003"]
            }
        }


class BatchTaskCreate(BaseModel):
    """创建批量任务请求"""
    dataset_name: str
    selected_cases: Optional[List[str]] = Field(default=None, description="可选，筛选特定case")

    class Config:
        json_schema_extra = {
            "example": {
                "dataset_name": "dataset_001",
                "selected_cases": ["case_001", "case_002"]
            }
        }


class BatchTask(BaseModel):
    """批量任务"""
    task_id: str
    dataset_name: str
    total_cases: int
    cases: List[CaseResult] = Field(default_factory=list)
    status: str = Field(default="pending", description="pending | processing | completed | failed")
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    progress: int = Field(default=0, ge=0, le=100)
    current_step: str = Field(default="")
    success: int = Field(default=0)
    failed: int = Field(default=0)

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "550e8400-e29b-41d4-a716-446655440000",
                "dataset_name": "dataset_001",
                "total_cases": 10,
                "cases": [],
                "status": "processing",
                "progress": 60,
                "current_step": "正在处理 case_007 (7/10)...",
                "success": 6,
                "failed": 0
            }
        }


class BatchTaskList(BaseModel):
    """批量任务列表响应"""
    total: int
    tasks: List[BatchTask]
