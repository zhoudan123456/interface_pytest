"""
任务管理API
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
from pathlib import Path
from app.models.task import get_task, TaskResponse
from app.services.pdf_extraction_service import PDFExtractionService

router = APIRouter(prefix='/tasks')


class ExtractRequest(BaseModel):
    """PDF提取请求"""
    zb_pdf_file_id: Optional[str] = None  # 招标文件ID（可选）
    tb_pdf_file_id: Optional[str] = None  # 投标文件ID（可选）


class ExtractResponse(BaseModel):
    """PDF提取响应"""
    code: int
    message: str
    data: Optional[dict] = None


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task_status(task_id: str):
    """查询任务状态

    Args:
        task_id: 任务ID

    Returns:
        任务详情
    """
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task


@router.get("", response_model=List[TaskResponse])
async def list_tasks(
    page: int = 1,
    page_size: int = 10
):
    """获取任务列表

    Args:
        page: 页码
        page_size: 每页大小

    Returns:
        任务列表
    """
    from app.models.task import tasks_db

    # 简单分页
    all_tasks = list(tasks_db.values())
    all_tasks.sort(key=lambda x: x.created_at, reverse=True)

    start = (page - 1) * page_size
    end = start + page_size

    return all_tasks[start:end]


@router.post("/extract", response_model=ExtractResponse)
async def extract_checkpoints(request: ExtractRequest):
    """从PDF提取检查点

    Args:
        request: 提取请求，包含招标文件ID和投标文件ID（至少提供一个）

    Returns:
        提取结果
    """
    from app.services.file_handler import FileHandlerService

    try:
        # 验证至少上传了一个文件
        if not request.zb_pdf_file_id and not request.tb_pdf_file_id:
            raise HTTPException(status_code=400, detail="请至少上传招标文件或投标文件")

        # 查找上传的文件
        file_handler = FileHandlerService()

        zb_file_info = None
        tb_file_info = None

        # 获取招标文件信息（如果提供）
        if request.zb_pdf_file_id:
            zb_file_info = file_handler.get_file_by_id(request.zb_pdf_file_id)
            if not zb_file_info:
                raise HTTPException(status_code=404, detail="招标文件不存在")
            # 支持PDF和DOCX格式
            filename_lower = zb_file_info['filename'].lower()
            if not (filename_lower.endswith('.pdf') or filename_lower.endswith('.docx')):
                raise HTTPException(status_code=400, detail="招标文件只支持PDF或DOCX格式")

        # 获取投标文件信息（如果提供）
        if request.tb_pdf_file_id:
            tb_file_info = file_handler.get_file_by_id(request.tb_pdf_file_id)
            if not tb_file_info:
                raise HTTPException(status_code=404, detail="投标文件不存在")
            # 支持PDF和DOCX格式
            filename_lower = tb_file_info['filename'].lower()
            if not (filename_lower.endswith('.pdf') or filename_lower.endswith('.docx')):
                raise HTTPException(status_code=400, detail="投标文件只支持PDF或DOCX格式")

        # 调用提取服务
        service = PDFExtractionService()
        result = service.extract_checkpoints_from_pdfs(
            zb_file_info['path'] if zb_file_info else None,
            tb_file_info['path'] if tb_file_info else None
        )

        if result['status'] == 'success':
            return ExtractResponse(
                code=200,
                message="检查点提取成功",
                data={
                    "task_id": result['task_id'],
                    "check_point_data": result.get('check_point_data'),
                    "bid_info_data": result.get('bid_info_data'),
                    "files": service.get_latest_extraction_files()
                }
            )
        else:
            raise HTTPException(status_code=500, detail=result.get('message'))

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"提取失败: {str(e)}")


@router.get("/extract/files")
async def list_extraction_files():
    """获取步骤1生成的文件列表

    Returns:
        可下载的文件列表
    """
    try:
        service = PDFExtractionService()
        files = service.get_all_extraction_files()
        return {
            "code": 200,
            "message": "success",
            "data": files
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文件列表失败: {str(e)}")


@router.get("/extract/download/{filename}")
async def download_extraction_file(filename: str):
    """下载步骤1生成的JSON文件

    Args:
        filename: 文件名

    Returns:
        JSON文件
    """
    try:
        service = PDFExtractionService()
        file_path = service.get_extraction_file_path(filename)

        if not file_path or not file_path.exists():
            raise HTTPException(status_code=404, detail="文件不存在")

        return FileResponse(
            path=file_path,
            filename=filename,
            media_type="application/json"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"下载失败: {str(e)}")
