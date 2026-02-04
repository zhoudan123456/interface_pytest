"""
文件上传API
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.services.file_handler import FileHandlerService
from app.models.report import FileUploadResponse, FileInfo
from app.models.task import create_task, TaskResponse

router = APIRouter()
file_handler = FileHandlerService()


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    type: str = Form(...)
):
    """上传文件接口

    Args:
        file: 上传的文件
        type: 文件类型 (excel/json/pdf)

    Returns:
        文件上传响应
    """
    try:
        # 保存文件
        file_info = await file_handler.save_upload_file(file, type)

        return FileUploadResponse(
            code=200,
            message="success",
            data=FileInfo(**file_info)
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"文件上传失败: {str(e)}"
        )


@router.post("/tasks/match", response_model=TaskResponse)
async def create_match_task(
    excel_file_id: str = Form(...),
    json_file_id: str = Form(...)
):
    """创建LLM匹配任务（同步执行）

    Args:
        excel_file_id: Excel文件ID
        json_file_id: JSON文件ID

    Returns:
        任务响应
    """
    from app.services.llm_matcher import LLMMatcherService
    from app.models.task import update_task

    # 获取文件路径
    excel_path = file_handler.get_file_path(excel_file_id)
    json_path = file_handler.get_file_path(json_file_id)

    if not excel_path:
        raise HTTPException(status_code=404, detail="Excel文件不存在")
    if not json_path:
        raise HTTPException(status_code=404, detail="JSON文件不存在")

    # 创建任务
    task = create_task(
        excel_file_id=excel_file_id,
        json_file_id=json_file_id,
        excel_path=str(excel_path),
        json_path=str(json_path)
    )

    # 同步执行LLM匹配任务
    try:
        # 更新任务状态为处理中
        update_task(
            task.task_id,
            status="processing",
            progress=10,
            current_step="初始化LLM匹配器..."
        )

        # 创建匹配服务实例
        matcher_service = LLMMatcherService()

        # 执行匹配（同步）
        result_path = matcher_service.run_matching_task(
            task_id=task.task_id,
            excel_path=str(excel_path),
            json_path=str(json_path)
        )

        # 获取更新后的任务信息
        task = update_task(
            task.task_id,
            result={"report_path": result_path}
        )

        return task

    except Exception as e:
        # 更新任务为失败状态
        update_task(
            task.task_id,
            status="failed",
            current_step=f"验证失败: {str(e)}",
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"LLM匹配失败: {str(e)}"
        )
