"""
LLM相关的Celery异步任务
"""
from app.tasks.celery_app import celery_app
from app.services.llm_matcher import LLMMatcherService
from app.models.task import update_task
import os


@celery_app.task(bind=True, max_retries=3)
def run_llm_match_task(self, task_id: str, excel_path: str, json_path: str):
    """执行LLM匹配的Celery任务

    Args:
        task_id: 任务ID
        excel_path: Excel文件路径
        json_path: JSON文件路径

    Returns:
        任务结果字典
    """
    try:
        # 初始化LLM匹配服务
        api_key = os.getenv("ZHIPUAI_API_KEY")
        service = LLMMatcherService(api_key)

        # 执行匹配任务
        result_path = service.run_matching_task(task_id, excel_path, json_path)

        return {
            "task_id": task_id,
            "status": "completed",
            "result_path": result_path
        }

    except Exception as exc:
        # 更新任务状态为失败
        update_task(
            task_id,
            status="failed",
            current_step=f"任务执行失败: {str(exc)}"
        )

        # 重试逻辑
        raise self.retry(exc=exc, countdown=60)
