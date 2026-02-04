"""
批量执行API
提供数据集管理和批量执行功能
"""
from __future__ import annotations

import asyncio
import json
import os
import tempfile
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.models.batch import BatchTask, DatasetInfo
from app.services.batch_processor import batch_processor

router = APIRouter(prefix="/batch", tags=["批量执行"])


# ========== 数据集管理 ==========

@router.post("/datasets/upload")
async def upload_dataset(file: UploadFile = File(...)):
    """上传数据集ZIP文件"""
    # 验证文件格式
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="只支持ZIP格式文件")

    # 保存到临时文件
    with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_file_path = tmp_file.name

    try:
        # 上传并解压数据集
        dataset_info = batch_processor.upload_dataset(
            tmp_file_path,
            file.filename
        )

        return {
            "code": 200,
            "message": "数据集上传成功",
            "data": dataset_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")
    finally:
        # 清理临时文件
        if os.path.exists(tmp_file_path):
            os.remove(tmp_file_path)


@router.get("/datasets")
async def list_datasets():
    """获取所有数据集列表"""
    try:
        datasets = batch_processor.list_datasets()
        return {
            "code": 200,
            "message": "success",
            "data": datasets
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取数据集列表失败: {str(e)}")


@router.get("/datasets/{dataset_name}")
async def get_dataset_info(dataset_name: str):
    """获取数据集详细信息"""
    try:
        dataset_info = batch_processor.get_dataset(dataset_name)
        if not dataset_info:
            raise HTTPException(status_code=404, detail="数据集不存在")

        return {
            "code": 200,
            "message": "success",
            "data": dataset_info
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取数据集信息失败: {str(e)}")


@router.delete("/datasets/{dataset_name}")
async def delete_dataset(dataset_name: str):
    """删除数据集"""
    try:
        success = batch_processor.delete_dataset(dataset_name)
        if not success:
            raise HTTPException(status_code=404, detail="数据集不存在")

        return {
            "code": 200,
            "message": "数据集删除成功",
            "data": None
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除数据集失败: {str(e)}")


# ========== 批量执行 ==========

class ExecuteRequest(BaseModel):
    """批量执行请求"""
    dataset_name: str
    selected_cases: Optional[list[str]] = None


@router.post("/execute")
async def create_batch_task(request: ExecuteRequest, background_tasks: BackgroundTasks):
    """创建批量执行任务

    注意：
    - 按顺序逐个执行case，每次只处理1个
    - 每次执行都会重新生成步骤1输出
    """
    try:
        # 创建任务
        task = batch_processor.create_batch_task(
            dataset_name=request.dataset_name,
            selected_cases=request.selected_cases
        )

        # 在后台执行任务
        background_tasks.add_task(execute_batch_task_async, task.task_id)

        return {
            "code": 200,
            "message": "批量任务创建成功",
            "data": task
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建任务失败: {str(e)}")


async def execute_batch_task_async(task_id: str):
    """异步执行批量任务"""
    from app.api.v1.batch_ws import broadcast_batch_progress

    # 定义进度回调
    async def progress_callback(task):
        # 通过WebSocket广播进度
        await broadcast_batch_progress(task_id, task)

    # 执行任务
    await batch_processor.execute_batch_task(task_id, progress_callback)


@router.get("/tasks/{task_id}")
async def get_batch_task_status(task_id: str):
    """获取批量任务状态"""
    try:
        task = batch_processor.get_batch_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")

        return {
            "code": 200,
            "message": "success",
            "data": task
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取任务状态失败: {str(e)}")


@router.get("/tasks")
async def list_batch_tasks(limit: int = 20):
    """获取批量任务历史"""
    try:
        tasks = batch_processor.list_batch_tasks(limit=limit)
        return {
            "code": 200,
            "message": "success",
            "data": tasks,
            "total": len(tasks)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取任务列表失败: {str(e)}")


@router.post("/tasks/{task_id}/cancel")
async def cancel_batch_task(task_id: str):
    """取消正在执行的批量任务"""
    try:
        task = batch_processor.get_batch_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")

        if task.status == "completed":
            raise HTTPException(status_code=400, detail="任务已完成，无法取消")

        # 更新任务状态为取消
        batch_processor.update_batch_task(
            task_id,
            status="failed",
            error="用户取消任务"
        )

        return {
            "code": 200,
            "message": "任务已取消",
            "data": None
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取消任务失败: {str(e)}")


# ========== 结果下载 ==========

@router.get("/tasks/{task_id}/results")
async def download_batch_results(task_id: str):
    """下载批量执行结果（ZIP打包）"""
    try:
        zip_path = batch_processor.get_batch_results_zip(task_id)
        if not zip_path:
            raise HTTPException(status_code=404, detail="任务不存在或结果不可用")

        return FileResponse(
            path=zip_path,
            filename=zip_path.name,
            media_type="application/zip"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"下载结果失败: {str(e)}")


@router.get("/tasks/{task_id}/report")
async def download_batch_report(task_id: str):
    """下载批量执行报告（JSON）"""
    try:
        task = batch_processor.get_batch_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")

        import json
        from datetime import datetime

        # 生成报告
        report = {
            "task_id": task.task_id,
            "dataset_name": task.dataset_name,
            "status": task.status,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "total_cases": task.total_cases,
            "success": task.success,
            "failed": task.failed,
            "progress": task.progress,
            "cases": [
                {
                    "case_name": c.case_name,
                    "status": c.status,
                    "step1_output": c.step1_output,
                    "step2_output": c.step2_output,
                    "error": c.error,
                    "start_time": c.start_time.isoformat() if c.start_time else None,
                    "end_time": c.end_time.isoformat() if c.end_time else None,
                }
                for c in task.cases
            ]
        }

        # 保存临时文件
        report_path = batch_processor.output_dir / f"batch_report_{task_id[:8]}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        return FileResponse(
            path=report_path,
            filename=f"batch_report_{task.task_id[:8]}.json",
            media_type="application/json"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"下载报告失败: {str(e)}")


@router.get("/tasks/{task_id}/cases/{case_name}/preview")
async def preview_case_file(
    task_id: str,
    case_name: str,
    file_type: str = "json"  # json | md
):
    """获取case输出文件的预览内容

    Returns:
        {
            "content": "文件内容字符串",
            "size": 12345,
            "lines": 150,
            "filename": "case_001_check_point.json"
        }
    """
    try:
        if file_type not in ["json", "md"]:
            raise HTTPException(status_code=400, detail="file_type必须是json或md")

        result = batch_processor.get_case_file_content(task_id, case_name, file_type)
        if not result:
            raise HTTPException(status_code=404, detail="文件不存在")

        return {
            "code": 200,
            "message": "success",
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"预览文件失败: {str(e)}")


@router.get("/tasks/{task_id}/cases/{case_name}/download")
async def download_case_file(
    task_id: str,
    case_name: str,
    file_type: str = "json"  # json | md
):
    """下载单个case的输出文件"""
    try:
        if file_type not in ["json", "md"]:
            raise HTTPException(status_code=400, detail="file_type必须是json或md")

        task = batch_processor.get_batch_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")

        case_path = batch_processor.datasets_dir / task.dataset_name / case_name
        if not case_path.exists():
            raise HTTPException(status_code=404, detail="case不存在")

        # 查找目标文件
        if file_type == "json":
            file_pattern = f"{case_name}_check_point_*.json"
            search_dir = batch_processor.output_dir.parent / "test_data" / "evaluation" / "responses"
        else:  # md
            file_pattern = f"{case_name}_validation_report_*.md"
            search_dir = case_path

        if not search_dir.exists():
            raise HTTPException(status_code=404, detail="文件目录不存在")

        files = list(search_dir.glob(file_pattern))
        if not files:
            # 尝试在case目录中查找
            files = list(case_path.rglob(f"*.{file_type}"))

        if not files:
            raise HTTPException(status_code=404, detail="文件不存在")

        # 取最新文件
        latest_file = sorted(files, key=lambda f: f.stat().st_mtime, reverse=True)[0]

        media_type = "application/json" if file_type == "json" else "text/markdown"
        return FileResponse(
            path=latest_file,
            filename=latest_file.name,
            media_type=media_type
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"下载文件失败: {str(e)}")
