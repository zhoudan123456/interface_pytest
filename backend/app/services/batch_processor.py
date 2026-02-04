"""
Web版批量处理器
处理数据集管理和批量执行任务
"""
import asyncio
import json
import shutil
import uuid
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from app.config import settings
from app.models.batch import BatchTask, CaseResult, DatasetInfo


class BatchProcessor:
    """Web版批量处理器"""

    def __init__(self):
        # 数据集目录
        self.datasets_dir = settings.PROJECT_ROOT / "datasets"
        self.datasets_dir.mkdir(parents=True, exist_ok=True)

        # 批量任务存储（内存，生产环境建议用Redis/数据库）
        self.batch_tasks_db: Dict[str, BatchTask] = {}

        # 输出目录
        self.output_dir = settings.OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # ========== 数据集管理 ==========

    def list_datasets(self) -> List[DatasetInfo]:
        """获取所有数据集列表"""
        datasets = []

        for item in self.datasets_dir.iterdir():
            if item.is_dir() and not item.name.startswith('_'):
                info = self._get_dataset_info(item)
                if info:
                    datasets.append(info)

        # 按创建时间倒序
        datasets.sort(key=lambda x: x.created_at, reverse=True)
        return datasets

    def _get_dataset_info(self, dataset_path: Path) -> Optional[DatasetInfo]:
        """获取数据集信息"""
        try:
            # 扫描cases
            cases = self._discover_cases(dataset_path)

            # 计算大小
            size_mb = sum(
                f.stat().st_size for f in dataset_path.rglob('*') if f.is_file()
            ) / (1024 * 1024)

            # 获取创建时间
            created_at = datetime.fromtimestamp(dataset_path.stat().st_ctime)

            return DatasetInfo(
                name=dataset_path.name,
                case_count=len(cases),
                created_at=created_at,
                size_mb=round(size_mb, 2),
                cases=[c.name for c in cases],
                path=str(dataset_path)
            )
        except Exception:
            return None

    def get_dataset(self, dataset_name: str) -> Optional[DatasetInfo]:
        """获取指定数据集信息"""
        dataset_path = self.datasets_dir / dataset_name
        if not dataset_path.exists():
            return None
        return self._get_dataset_info(dataset_path)

    def _discover_cases(self, dataset_path: Path) -> List[Path]:
        """扫描数据集目录，发现所有case"""
        cases = []
        for item in dataset_path.iterdir():
            if item.is_dir() and not item.name.startswith('_'):
                cases.append(item)
        return sorted(cases)

    def upload_dataset(self, zip_file_path: str, filename: str) -> DatasetInfo:
        """上传并解压数据集ZIP文件

        Args:
            zip_file_path: ZIP文件路径
            filename: 原始文件名

        Returns:
            数据集信息
        """
        # 生成数据集名称（去掉.zip后缀）
        dataset_name = Path(filename).stem

        # 如果已存在，添加时间戳
        if (self.datasets_dir / dataset_name).exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dataset_name = f"{dataset_name}_{timestamp}"

        # 解压目录
        extract_path = self.datasets_dir / dataset_name

        try:
            # 解压文件
            with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)

            # 验证结构
            cases = self._discover_cases(extract_path)
            if not cases:
                raise ValueError("数据集为空，未找到任何case目录")

            return self._get_dataset_info(extract_path)

        except Exception as e:
            # 解压失败，清理目录
            if extract_path.exists():
                shutil.rmtree(extract_path)
            raise e

    def delete_dataset(self, dataset_name: str) -> bool:
        """删除数据集"""
        dataset_path = self.datasets_dir / dataset_name
        if not dataset_path.exists():
            return False

        shutil.rmtree(dataset_path)
        return True

    # ========== 批量任务管理 ==========

    def create_batch_task(
        self,
        dataset_name: str,
        selected_cases: Optional[List[str]] = None
    ) -> BatchTask:
        """创建批量任务

        Args:
            dataset_name: 数据集名称
            selected_cases: 可选，筛选特定case

        Returns:
            批量任务
        """
        # 验证数据集
        dataset_path = self.datasets_dir / dataset_name
        if not dataset_path.exists():
            raise ValueError(f"数据集不存在: {dataset_name}")

        # 扫描cases
        all_cases = self._discover_cases(dataset_path)

        # 筛选cases
        if selected_cases:
            all_cases = [c for c in all_cases if c.name in selected_cases]

        if not all_cases:
            raise ValueError("没有可执行的case")

        # 创建任务
        task_id = str(uuid.uuid4())
        task = BatchTask(
            task_id=task_id,
            dataset_name=dataset_name,
            total_cases=len(all_cases),
            cases=[CaseResult(case_name=c.name) for c in all_cases],
            status="pending",
            created_at=datetime.now(),
            progress=0,
            current_step="",
            success=0,
            failed=0
        )

        self.batch_tasks_db[task_id] = task
        return task

    def get_batch_task(self, task_id: str) -> Optional[BatchTask]:
        """获取批量任务"""
        return self.batch_tasks_db.get(task_id)

    def list_batch_tasks(self, limit: int = 20) -> List[BatchTask]:
        """获取批量任务列表"""
        tasks = list(self.batch_tasks_db.values())
        tasks.sort(key=lambda x: x.created_at or datetime.min, reverse=True)
        return tasks[:limit]

    def update_batch_task(self, task_id: str, **kwargs) -> Optional[BatchTask]:
        """更新批量任务"""
        task = self.batch_tasks_db.get(task_id)
        if not task:
            return None

        for key, value in kwargs.items():
            if hasattr(task, key):
                setattr(task, key, value)

        return task

    # ========== 批量执行 ==========

    async def execute_batch_task(
        self,
        task_id: str,
        progress_callback=None
    ) -> BatchTask:
        """执行批量处理任务（串行，逐个执行）

        Args:
            task_id: 任务ID
            progress_callback: 进度回调函数

        Returns:
            更新后的任务
        """
        task = self.batch_tasks_db.get(task_id)
        if not task:
            raise ValueError(f"任务不存在: {task_id}")

        dataset_path = self.datasets_dir / task.dataset_name

        try:
            # 更新任务状态
            task.status = "processing"
            task.started_at = datetime.now()
            task.current_step = "开始批量处理..."

            if progress_callback:
                await progress_callback(task)

            total = len(task.cases)

            # 串行处理，逐个执行case
            for i, case_result in enumerate(task.cases):
                case_path = dataset_path / case_result.case_name

                # 更新当前处理进度
                task.current_step = f"正在处理 {case_result.case_name} ({i+1}/{total})..."
                case_result.status = "processing"
                case_result.start_time = datetime.now()

                if progress_callback:
                    await progress_callback(task)

                # 执行单个case
                try:
                    result = await self._process_single_case(case_path)

                    # 更新case状态
                    case_result.status = "success"
                    case_result.step1_output = result.get("step1_output")
                    case_result.step2_output = result.get("step2_output")
                    case_result.end_time = datetime.now()

                    task.success += 1

                except Exception as e:
                    case_result.status = "failed"
                    case_result.error = str(e)
                    case_result.end_time = datetime.now()
                    task.failed += 1

                # 更新任务进度
                task.progress = int((i + 1) / total * 100)
                task.current_step = f"已完成 {case_result.case_name} ({i+1}/{total})..."

                if progress_callback:
                    await progress_callback(task)

            # 任务完成
            task.status = "completed"
            task.completed_at = datetime.now()
            task.current_step = "批量处理完成"
            task.progress = 100

            if progress_callback:
                await progress_callback(task)

        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            task.current_step = f"批量处理失败: {str(e)}"

            if progress_callback:
                await progress_callback(task)

        return task

    async def _process_single_case(self, case_path: Path) -> Dict:
        """处理单个case（两步流程）

        步骤1: 从PDF提取检查点，生成JSON
        步骤2: 使用Excel和JSON进行LLM验证，生成MD报告

        Args:
            case_path: case目录路径

        Returns:
            处理结果
        """
        # ========== 步骤1: 查找PDF/DOCX文件并提取检查点 ==========
        # 支持PDF和DOCX格式
        zb_files = (
            list(case_path.glob("*招标*.pdf")) +
            list(case_path.glob("*招标*.docx")) +
            list(case_path.glob("*zb*.pdf")) +
            list(case_path.glob("*zb*.docx"))
        )
        tb_files = (
            list(case_path.glob("*投标*.pdf")) +
            list(case_path.glob("*投标*.docx")) +
            list(case_path.glob("*tb*.pdf")) +
            list(case_path.glob("*tb*.docx"))
        )

        # 如果没有找到中文文件名，尝试通用PDF/DOCX
        if not zb_files:
            zb_files = list(case_path.glob("*.pdf"))[:1] + list(case_path.glob("*.docx"))[:1]
            if zb_files:
                zb_files = [zb_files[0]]
        if not tb_files:
            tb_files = list(case_path.glob("*.pdf"))[1:2] + list(case_path.glob("*.docx"))[1:2]
            if tb_files:
                tb_files = [tb_files[0]]

        zb_doc_path = zb_files[0] if zb_files else None
        tb_doc_path = tb_files[0] if tb_files else None

        if not zb_doc_path and not tb_doc_path:
            raise FileNotFoundError("未找到招标/投标文件（支持PDF和DOCX格式）")

        # 导入提取服务
        from app.services.pdf_extraction_service import PDFExtractionService

        service = PDFExtractionService()

        # 步骤1: 执行文档提取（支持PDF和DOCX）
        # 直接输出到case目录
        extract_result = service.extract_checkpoints_from_pdfs(
            str(zb_doc_path) if zb_doc_path else None,
            str(tb_doc_path) if tb_doc_path else None,
            output_dir=str(case_path)  # 直接输出到case目录
        )

        if extract_result['status'] != 'success':
            raise Exception(f"步骤1提取失败: {extract_result.get('message', '未知错误')}")

        # 从case目录获取步骤1生成的JSON文件
        step1_json_files = list(case_path.glob("*_check_point_*.json"))
        if not step1_json_files:
            raise Exception("步骤1未生成JSON文件")

        # 取最新的文件
        step1_json_file = sorted(step1_json_files, key=lambda f: f.stat().st_mtime)[-1]
        json_file_path = step1_json_file
        step1_filename = step1_json_file.name
        print(f"[DEBUG] Step1 generated: {step1_filename}")

        # ========== 步骤2: 查找Excel文件并执行LLM验证 ==========
        excel_files = list(case_path.glob("*.xlsx")) + list(case_path.glob("*.xls"))

        if not excel_files:
            raise FileNotFoundError("未找到人工标注Excel文件")

        excel_file_path = excel_files[0]

        # 导入LLM匹配服务
        from app.services.llm_matcher import LLMMatcherService
        from datetime import datetime

        # 创建匹配器实例
        matcher_service = LLMMatcherService()

        # 生成输出文件路径 - 保存到case目录下（确保使用绝对路径）
        # 在任何os.chdir()之前计算绝对路径
        case_name = case_path.name
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        # 直接使用绝对路径，不使用resolve()避免受工作目录变化影响
        if not case_path.is_absolute():
            output_file = case_path.resolve() / f'{case_name}_validation_report_{timestamp}.md'
        else:
            output_file = case_path / f'{case_name}_validation_report_{timestamp}.md'

        # 确保case目录存在
        case_path.mkdir(parents=True, exist_ok=True)

        # 打印调试信息
        print(f"[DEBUG] Case path: {case_path}")
        print(f"[DEBUG] Case path is_absolute: {case_path.is_absolute()}")
        print(f"[DEBUG] Output file: {output_file}")
        print(f"[DEBUG] Output file is_absolute: {output_file.is_absolute()}")

        # 导入匹配器
        from ai_test_scripts.llm_matcher_zhipuai import ZhipuAILMMatcher

        # 创建匹配器实例
        matcher = ZhipuAILMMatcher(settings.ZHIPUAI_API_KEY)

        # 步骤2: 执行LLM匹配验证
        actual_output_file = matcher.match_all_checkpoints(
            str(excel_file_path),
            str(json_file_path),
            output_file=str(output_file)
        )

        # 验证步骤2是否成功执行
        if actual_output_file is False or actual_output_file is None:
            # 方法返回了 False 或 None，表示执行失败
            # 检查是否至少生成了预期的文件
            if not output_file.exists():
                raise Exception("步骤2 LLM验证失败，未生成Markdown报告")
            # 如果文件存在，继续使用预期的文件名
            step2_md_file = output_file.name
        else:
            # 方法返回了文件路径，使用返回的路径
            import pathlib
            actual_path = pathlib.Path(actual_output_file)
            if actual_path.exists():
                step2_md_file = actual_path.name
            else:
                # 返回的路径不存在，检查预期的文件
                if output_file.exists():
                    step2_md_file = output_file.name
                else:
                    raise Exception(f"步骤2生成的报告文件不存在: {actual_output_file}")

        return {
            "step1_output": step1_filename,
            "step2_output": step2_md_file
        }

    # ========== 结果下载 ==========

    def get_batch_results_zip(self, task_id: str) -> Optional[Path]:
        """打包批量执行结果为ZIP

        Args:
            task_id: 任务ID

        Returns:
            ZIP文件路径
        """
        task = self.batch_tasks_db.get(task_id)
        if not task:
            return None

        # 创建临时ZIP文件
        zip_path = self.output_dir / f"{task.dataset_name}_results_{task_id[:8]}.zip"

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # 添加响应文件
            response_dir = settings.PROJECT_ROOT / "test_data" / "evaluation" / "responses"
            if response_dir.exists():
                for file_path in response_dir.glob("*.json"):
                    zipf.write(file_path, file_path.name)

            # 添加报告文件
            for case_result in task.cases:
                if case_result.status == "success":
                    case_path = self.datasets_dir / task.dataset_name / case_result.case_name

                    # 添加JSON文件（check_point和bid_info）
                    for file_path in case_path.rglob("*.json"):
                        if "check_point" in file_path.name or "bid_info" in file_path.name:
                            zipf.write(file_path, f"{case_result.case_name}/{file_path.name}")

                    # 添加Markdown验证报告
                    for file_path in case_path.glob("*.md"):
                        if "validation_report" in file_path.name:
                            zipf.write(file_path, f"{case_result.case_name}/{file_path.name}")

        return zip_path

    def get_case_file_content(
        self,
        task_id: str,
        case_name: str,
        file_type: str
    ) -> Optional[Dict]:
        """获取case输出文件的预览内容

        Args:
            task_id: 任务ID
            case_name: case名称
            file_type: 文件类型 (json | md)

        Returns:
            文件内容信息
        """
        task = self.batch_tasks_db.get(task_id)
        if not task:
            return None

        case_path = self.datasets_dir / task.dataset_name / case_name
        if not case_path.exists():
            return None

        # 查找目标文件
        if file_type == "json":
            file_pattern = f"{case_name}_check_point_*.json"
            search_dir = settings.PROJECT_ROOT / "test_data" / "evaluation" / "responses"
        else:  # md
            file_pattern = f"{case_name}_validation_report_*.md"
            search_dir = case_path

        if not search_dir.exists():
            return None

        files = list(search_dir.glob(file_pattern))
        if not files:
            # 尝试在case目录中查找
            files = list(case_path.rglob(f"*{file_type}"))

        if not files:
            return None

        # 取最新文件
        latest_file = sorted(files, key=lambda f: f.stat().st_mtime, reverse=True)[0]

        # 读取文件内容
        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                content = f.read()

            return {
                "content": content,
                "size": latest_file.stat().st_size,
                "lines": content.count('\n') + 1,
                "filename": latest_file.name,
                "encoding": "utf-8"
            }
        except Exception:
            return None


# 全局实例
batch_processor = BatchProcessor()
