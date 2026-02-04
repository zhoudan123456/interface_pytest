"""
LLM匹配服务 - 封装现有匹配逻辑
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from ai_test_scripts.llm_matcher_zhipuai import ZhipuAILMMatcher
from app.models.task import update_task
from app.config import settings


class LLMMatcherService:
    """LLM匹配服务"""

    def __init__(self, api_key: str = None):
        """初始化服务

        Args:
            api_key: 智谱AI API密钥
        """
        self.api_key = api_key or settings.ZHIPUAI_API_KEY
        if not self.api_key:
            raise ValueError("智谱AI API密钥未设置")

    def run_matching_task(
        self,
        task_id: str,
        excel_path: str,
        json_path: str
    ) -> str:
        """执行LLM匹配任务

        Args:
            task_id: 任务ID
            excel_path: Excel文件路径
            json_path: JSON文件路径

        Returns:
            生成的报告文件路径
        """
        try:
            # 更新任务状态为处理中
            update_task(
                task_id,
                status="processing",
                progress=10,
                current_step="初始化LLM匹配器..."
            )

            # 创建匹配器实例
            matcher = ZhipuAILMMatcher(self.api_key)

            # 生成输出文件路径（使用backend的outputs目录）
            from datetime import datetime
            import pathlib

            excel_basename = pathlib.Path(excel_path).stem
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = settings.OUTPUT_DIR / f'{excel_basename}_validation_{timestamp}.md'

            # 确保输出目录存在
            settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

            # 更新进度
            update_task(
                task_id,
                progress=20,
                current_step="正在调用智谱AI进行语义匹配..."
            )

            # 执行匹配（传入正确的输出路径）
            result_path = matcher.match_all_checkpoints(
                excel_path,
                json_path,
                output_file=str(output_file)
            )

            # 保存相对路径到任务结果（相对于项目根目录）
            relative_path = str(output_file.relative_to(settings.PROJECT_ROOT))

            # 更新任务为完成状态
            update_task(
                task_id,
                status="completed",
                progress=100,
                current_step="验证完成",
                result={"report_path": relative_path}
            )

            return relative_path

        except Exception as e:
            # 更新任务为失败状态
            update_task(
                task_id,
                status="failed",
                current_step=f"验证失败: {str(e)}",
                error=str(e)
            )
            raise
