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
        运行pytest工作流提取检查点

        Args:
            pdf_file_path: PDF文件路径
            task_id: 任务ID

        Returns:
            提取结果字典
        """
        try:
            # 切换到测试目录
            os.chdir(self.test_dir)

            # 运行pytest工作流
            cmd = [
                sys.executable, "-m", "pytest",
                "test_cases/workflows/test_bid_check_workflow.py::TestBidCheckWorkflow::test_01_upload_documents",
                "-v", "-s",
                f"--zb-file={pdf_file_path}"
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )

            if result.returncode != 0:
                raise Exception(f"pytest执行失败: {result.stderr}")

            # 运行后续测试步骤
            self._run_followup_tests()

            # 读取生成的响应文件
            return self._read_extraction_results()

        except subprocess.TimeoutExpired:
            raise Exception("API提取超时")
        except Exception as e:
            raise Exception(f"pytest工作流执行失败: {str(e)}")

    def _run_pytest_workflow_with_both_files(self, zb_pdf_path: Optional[str] = None, tb_pdf_path: Optional[str] = None, task_id: str = None, output_dir: Optional[str] = None) -> Dict:
        """
        运行pytest工作流提取检查点（使用招标文件和投标文件）

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

            # 构建pytest命令参数
            cmd = [
                sys.executable, "-m", "pytest",
                "test_cases/workflows/test_bid_check_workflow.py::TestBidCheckWorkflow::test_01_upload_documents",
                "-v", "-s"
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
                timeout=300,  # 5分钟超时
                env=env
            )

            if result.returncode != 0:
                raise Exception(f"pytest执行失败: {result.stderr}")

            # 运行后续测试步骤
            self._run_followup_tests()

            # 读取生成的响应文件
            return self._read_extraction_results()

        except subprocess.TimeoutExpired:
            raise Exception("API提取超时")
        except Exception as e:
            raise Exception(f"pytest工作流执行失败: {str(e)}")

    def _run_followup_tests(self):
        """运行后续测试步骤"""
        tests = [
            "test_cases/workflows/test_bid_check_workflow.py::TestBidCheckWorkflow::test_03_start_check_task",
            "test_cases/workflows/test_bid_check_workflow.py::TestBidCheckWorkflow::test_04_query_analysis_status",
            "test_cases/workflows/test_bid_check_workflow.py::TestBidCheckWorkflow::test_05_check_check_point",
            "test_cases/workflows/test_bid_check_workflow.py::TestBidCheckWorkflow::test_06_get_bid_info"
        ]

        for test in tests:
            cmd = [sys.executable, "-m", "pytest", test, "-v", "-s"]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10分钟超时
            )

            if result.returncode != 0:
                raise Exception(f"测试步骤失败: {test}")

    def _read_extraction_results(self) -> Dict:
        """读取提取结果文件"""
        response_dir = self.test_dir / "test_data" / "evaluation" / "responses"

        if not response_dir.exists():
            raise Exception("响应数据目录不存在")

        # 读取最新的响应文件
        check_point_files = sorted(response_dir.glob("*_check_point_*.json"))
        bid_info_files = sorted(response_dir.glob("*_bid_info_*.json"))

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
