"""
PDF检查点提取服务
集成现有的pytest API测试流程
"""
import json
import os
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Dict, List, Optional

from app.config import settings


class PDFExtractionService:
    """PDF检查点提取服务"""

    def __init__(self):
        self.base_dir = Path(__file__).parent.parent.parent
        self.test_dir = self.base_dir.parent
        self.output_dir = settings.OUTPUT_DIR

    def extract_checkpoints_from_pdf(self, pdf_file_path: str) -> Dict:
        """
        从PDF文件中提取检查点

        Args:
            pdf_file_path: PDF文件路径

        Returns:
            包含提取结果的字典
        """
        try:
            # 验证文件存在
            if not os.path.exists(pdf_file_path):
                raise FileNotFoundError(f"PDF文件不存在: {pdf_file_path}")

            # 生成任务ID
            task_id = str(uuid.uuid4())

            # 调用pytest工作流进行API提取
            result = self._run_pytest_workflow(pdf_file_path, task_id)

            return {
                "task_id": task_id,
                "status": "success",
                "check_point_data": result.get("check_point"),
                "bid_info_data": result.get("bid_info"),
                "message": "检查点提取成功"
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"提取失败: {str(e)}"
            }

    def extract_checkpoints_from_pdfs(self, zb_pdf_path: Optional[str] = None, tb_pdf_path: Optional[str] = None, output_dir: Optional[str] = None) -> Dict:
        """
        从招标文件和投标文件中提取检查点

        Args:
            zb_pdf_path: 招标文件PDF路径（可选）
            tb_pdf_path: 投标文件PDF路径（可选）
            output_dir: 输出目录路径（可选，默认为test_data/evaluation/responses）

        Returns:
            包含提取结果的字典
        """
        try:
            # 验证至少有一个文件
            if not zb_pdf_path and not tb_pdf_path:
                return {
                    "status": "error",
                    "message": "请至少提供一个PDF文件"
                }

            # 验证文件存在
            if zb_pdf_path and not os.path.exists(zb_pdf_path):
                return {
                    "status": "error",
                    "message": f"招标文件不存在: {zb_pdf_path}"
                }
            if tb_pdf_path and not os.path.exists(tb_pdf_path):
                return {
                    "status": "error",
                    "message": f"投标文件不存在: {tb_pdf_path}"
                }

            # 生成任务ID
            task_id = str(uuid.uuid4())

            # 调用pytest工作流进行API提取
            result = self._run_pytest_workflow_with_both_files(zb_pdf_path, tb_pdf_path, task_id, output_dir)

            return {
                "task_id": task_id,
                "status": "success",
                "check_point_data": result.get("check_point"),
                "bid_info_data": result.get("bid_info"),
                "message": "检查点提取成功"
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"提取失败: {str(e)}"
            }

    def _run_pytest_workflow(self, pdf_file_path: str, task_id: str) -> Dict:
        """
        运行pytest工作流提取检查点（单个PDF文件）

        在单个pytest会话中运行所有相关测试，确保状态通过YAML配置文件正确传递

        Args:
            pdf_file_path: PDF文件路径
            task_id: 任务ID

        Returns:
            提取结果字典
        """
        try:
            # 切换到测试目录
            os.chdir(self.test_dir)

            # 运行pytest工作流 - 一次性运行所有需要的测试
            cmd = [
                sys.executable, "-m", "pytest",
                "test_cases/workflows/test_bid_check_workflow.py::TestBidCheckWorkflow",
                "-v", "-s",
                "-k", "test_01 or test_03 or test_04 or test_05 or test_06",  # 跳过test_02
                f"--zb-file={pdf_file_path}"
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=1200  # 20分钟超时（包含API处理时间）
            )

            # 检查执行结果
            if result.returncode != 0:
                output = result.stdout + result.stderr
                # 检查是否有关键错误
                if "test_01" not in output or "PASSED" not in output:
                    raise Exception(f"pytest执行失败: {output[-500:]}")

            # 读取生成的响应文件
            return self._read_extraction_results()

        except subprocess.TimeoutExpired:
            raise Exception("API提取超时")
        except Exception as e:
            raise Exception(f"pytest工作流执行失败: {str(e)}")

    def _run_pytest_workflow_with_both_files(self, zb_pdf_path: Optional[str] = None, tb_pdf_path: Optional[str] = None, task_id: str = None, output_dir: Optional[str] = None) -> Dict:
        """
        运行pytest工作流提取检查点（使用招标文件和投标文件）

        在单个pytest会话中运行所有相关测试，确保状态通过YAML配置文件正确传递

        Args:
            zb_pdf_path: 招标文件PDF路径（可选）
            tb_pdf_path: 投标文件PDF路径（可选）
            task_id: 任务ID
            output_dir: 输出目录路径（可选）

        Returns:
            提取结果字典
        """
        try:
            # 切换到测试目录
            os.chdir(self.test_dir)

            # 构建pytest命令参数 - 一次性运行所有需要的测试
            # 使用 -k 参数一次性运行所有相关测试，确保它们在同一进程中执行
            cmd = [
                sys.executable, "-m", "pytest",
                "test_cases/workflows/test_bid_check_workflow.py::TestBidCheckWorkflow",
                "-v", "-s",
                "-k", "test_01 or test_03 or test_04 or test_05 or test_06"  # 跳过test_02
            ]

            # 根据提供的文件添加命令行参数
            if zb_pdf_path:
                cmd.append(f"--zb-file={zb_pdf_path}")
            if tb_pdf_path:
                cmd.append(f"--tb-file={tb_pdf_path}")

            # 设置环境变量，让pytest输出到指定目录
            env = os.environ.copy()
            if output_dir:
                env['BID_CHECK_OUTPUT_DIR'] = output_dir

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=1200,  # 20分钟超时（包含API处理时间）
                env=env
            )

            # 检查执行结果
            if result.returncode != 0:
                output = result.stdout + result.stderr
                # 检查是否有关键错误
                # 如果test_01成功但后续测试因API状态失败，仍然尝试读取结果
                if "test_01" not in output or "PASSED" not in output:
                    raise Exception(f"pytest执行失败: {output[-500:]}")

            # 读取生成的响应文件
            return self._read_extraction_results(output_dir)

        except subprocess.TimeoutExpired:
            raise Exception("API提取超时")
        except Exception as e:
            raise Exception(f"pytest工作流执行失败: {str(e)}")

    def _read_extraction_results(self, output_dir: Optional[str] = None) -> Dict:
        """读取提取结果文件

        Args:
            output_dir: 可选的输出目录路径。如果为None，使用默认目录

        Returns:
            提取结果字典
        """
        # 如果指定了输出目录，使用它；否则使用默认目录
        if output_dir:
            response_dir = Path(output_dir)
        else:
            response_dir = self.test_dir / "test_data" / "evaluation" / "responses"

        if not response_dir.exists():
            raise Exception(f"响应数据目录不存在: {response_dir}")

        # 读取最新的响应文件（按修改时间排序）
        check_point_files = sorted(response_dir.glob("*_check_point_*.json"), key=lambda f: f.stat().st_mtime)
        bid_info_files = sorted(response_dir.glob("*_bid_info_*.json"), key=lambda f: f.stat().st_mtime)

        result = {}

        if check_point_files:
            latest_check_point = check_point_files[-1]
            with open(latest_check_point, 'r', encoding='utf-8') as f:
                result["check_point"] = json.load(f)

        if bid_info_files:
            latest_bid_info = bid_info_files[-1]
            with open(latest_bid_info, 'r', encoding='utf-8') as f:
                result["bid_info"] = json.load(f)

        return result

    def get_all_extraction_files(self) -> List[Dict]:
        """获取所有步骤1生成的文件列表

        Returns:
            文件信息列表，包含文件名、文件路径、修改时间等
        """
        response_dir = self.test_dir / "test_data" / "evaluation" / "responses"

        if not response_dir.exists():
            return []

        files = []
        for file_path in response_dir.glob("*.json"):
            stat = file_path.stat()
            files.append({
                "filename": file_path.name,
                "size": stat.st_size,
                "modified_time": stat.st_mtime,
                "type": "check_point" if "check_point" in file_path.name else "bid_info"
            })

        # 按修改时间倒序排列
        files.sort(key=lambda x: x["modified_time"], reverse=True)
        return files

    def get_latest_extraction_files(self) -> Dict:
        """获取最新生成的文件信息

        Returns:
            包含最新文件路径的字典
        """
        response_dir = self.test_dir / "test_data" / "evaluation" / "responses"

        if not response_dir.exists():
            return {}

        # 按修改时间排序，获取最新的文件
        check_point_files = sorted(response_dir.glob("*_check_point_*.json"), key=lambda f: f.stat().st_mtime)
        bid_info_files = sorted(response_dir.glob("*_bid_info_*.json"), key=lambda f: f.stat().st_mtime)

        result = {}

        if check_point_files:
            result["check_point_file"] = check_point_files[-1].name

        if bid_info_files:
            result["bid_info_file"] = bid_info_files[-1].name

        return result

    def get_extraction_file_path(self, filename: str) -> Optional[Path]:
        """获取步骤1生成文件的完整路径

        Args:
            filename: 文件名

        Returns:
            文件的完整路径，如果文件不存在则返回None
        """
        response_dir = self.test_dir / "test_data" / "evaluation" / "responses"
        file_path = response_dir / filename

        if file_path.exists():
            return file_path
        return None
