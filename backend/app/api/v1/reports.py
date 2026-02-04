"""
报告下载API
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
from typing import List, Dict

router = APIRouter()


@router.get("/files")
async def list_reports():
    """获取所有验证报告文件列表

    Returns:
        报告文件列表
    """
    from app.config import settings

    output_dir = Path(settings.OUTPUT_DIR)
    if not output_dir.exists():
        return {"code": 200, "message": "success", "data": []}

    files = []
    for file_path in output_dir.glob("*_validation_*.md"):
        stat = file_path.stat()
        files.append({
            "filename": file_path.name,
            "size": stat.st_size,
            "modified_time": stat.st_mtime,
            "type": "validation_report"
        })

    # 按修改时间倒序排列
    files.sort(key=lambda x: x["modified_time"], reverse=True)

    return {"code": 200, "message": "success", "data": files}


@router.get("/{task_id}")
async def download_report(task_id: str):
    """下载验证报告

    Args:
        task_id: 任务ID

    Returns:
        Markdown文件
    """
    from app.models.task import get_task
    from app.config import settings

    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.status != "completed":
        raise HTTPException(status_code=400, detail="任务尚未完成")

    if not task.result or "report_path" not in task.result:
        raise HTTPException(status_code=404, detail="报告文件不存在")

    # 支持相对路径和绝对路径
    report_path_str = task.result["report_path"]
    report_path = Path(report_path_str)

    # 如果是相对路径，从项目根目录解析
    if not report_path.is_absolute():
        # 新数据：从项目根目录（outputs/）解析
        project_root_relative = settings.PROJECT_ROOT / report_path_str
        # 老数据：从backend目录（backend/outputs/）解析
        backend_relative = settings.BASE_DIR / report_path_str

        if project_root_relative.exists():
            report_path = project_root_relative
        elif backend_relative.exists():
            report_path = backend_relative

    if not report_path.exists():
        raise HTTPException(status_code=404, detail="报告文件不存在")

    return FileResponse(
        path=report_path,
        filename=report_path.name,
        media_type="text/markdown"
    )


@router.get("/download/{filename}")
async def download_report_by_filename(filename: str):
    """通过文件名下载验证报告

    Args:
        filename: 文件名

    Returns:
        Markdown文件
    """
    from app.config import settings

    output_dir = Path(settings.OUTPUT_DIR)
    file_path = output_dir / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="text/markdown"
    )
