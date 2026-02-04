# Web版批量执行方案

## 一、系统概述

### 1.1 功能定位

将命令行批量执行功能升级为Web界面，允许非技术人员通过浏览器一键运行所有测试用例，实时查看进度，并下载批量处理结果。

### 1.2 核心特性

- 📁 **数据集管理**：支持上传、预览、删除测试数据集
- 🚀 **一键执行**：简单配置后启动批量处理任务
- 📊 **实时进度**：WebSocket推送任务进度，实时显示处理状态
- 📈 **可视化结果**：图表展示成功/失败统计
- 👁️ **文件预览**：在线预览JSON和MD报告，无需下载 ⭐
- 💾 **结果下载**：批量下载生成的JSON和MD报告文件
- 🔍 **结果对比**：对比不同批次执行结果
- 🔄 **任务历史**：查看历史批量执行记录

---

## 二、用户体验流程

### 2.1 完整操作流程

```
┌─────────────────────────────────────────────────────────┐
│              用户操作流程                                │
└─────────────────────────────────────────────────────────┘

1. 访问批量执行页面
   ├─ 点击"批量执行"导航菜单
   └─ 进入批量测试管理界面

2. 上传/选择数据集
   ├─ 方式1：上传新的数据集ZIP包
   ├─ 方式2：选择服务器已有数据集
   └─ 预览数据集包含的case列表

3. 配置执行参数
   └─ 选择特定case（可选，默认全部执行）

4. 启动批量执行
   ├─ 点击"开始执行"按钮
   ├─ 实时查看处理进度
   ├─ 查看当前处理步骤
   └─ 监控成功/失败数量

5. 查看执行结果
   ├─ 查看汇总统计
   ├─ 查看每个case的详细结果
   ├─ 下载批量处理报告
   └─ 下载生成的JSON和MD文件

6. 管理历史记录
   ├─ 查看历史执行记录
   ├─ 对比不同执行结果
   └─ 重新执行历史任务
```

### 2.2 页面布局设计

```
┌──────────────────────────────────────────────────────────┐
│  批量执行 - 招标文件检查点验证系统                        │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐  ┌─────────────────────────────────┐  │
│  │              │  │  数据集选择                      │  │
│  │   步骤导航   │  │  ┌──────────────────────────┐   │  │
│  │              │  │  │ 📁 dataset_001           │   │  │
│  │ 1. 选择数据集 │  │  │   10个case • 2026-02-04  │   │  │
│  │ ✓            │  │  └──────────────────────────┘   │  │
│  │              │  │  ┌──────────────────────────┐   │  │
│  │ 2. 配置参数   │  │  │ 📁 dataset_002           │   │  │
│  │ ✓            │  │  │   25个case • 2026-02-03  │   │  │
│  │              │  │  └──────────────────────────┘   │  │
│  │ 3. 查看结果   │  │  [+ 上传新数据集]              │  │
│  │              │  └─────────────────────────────────┘  │
│  │              │                                        │
│  └──────────────┘  ┌─────────────────────────────────┐  │
│                    │  执行配置                          │  │
│                    │  筛选: [case_001, case_002...]    │  │
│                    │  [开始执行] [重置]                │  │
│                    │                                    │  │
│                    │  💡 按顺序逐个执行，每次1个case    │  │
│                    │  💡 每次执行都会重新生成步骤1输出   │  │
│                    └─────────────────────────────────┘  │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │  执行进度                                          │  │
│  │  ████████████████░░░░░░░░░░░░░░░  60% (6/10)      │  │
│  │  当前: 正在处理 case_007 - AI语义匹配...          │  │
│  └──────────────────────────────────────────────────┘  │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │  执行结果                                          │  │
│  │  ┌────────────────────────────────────────────┐   │  │
│  │  │ 📊 统计汇总                                │   │  │
│  │  │ 总计: 10 | ✅成功: 8 | ❌失败: 2           │   │  │
│  │  └────────────────────────────────────────────┘   │  │
│  │                                                    │  │
│  │  Case ID        状态        步骤1        步骤2     │  │
│  │  case_001       ✅成功       ✓新提取      ✓完成    │  │
│  │  case_002       ✅成功       ✓新提取      ✓完成    │  │
│  │  case_003       ❌失败      ✗文件缺失    -        │  │
│  │  case_004       ⏳处理中    ⏳提取中...   -        │  │
│  │                                                    │  │
│  │  [下载所有结果] [导出报告]                         │  │
│  └──────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

---

## 三、后端API设计

### 3.1 API端点结构

```python
# backend/app/api/v1/batch.py

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from typing import Optional
import zipfile
import shutil

router = APIRouter(prefix="/batch", tags=["批量执行"])

# ========== 数据集管理 ==========

@router.post("/datasets/upload")
async def upload_dataset(file: UploadFile = File(...)):
    """上传数据集ZIP文件"""
    # 1. 验证文件格式（ZIP）
    # 2. 解压到 datasets/ 目录
    # 3. 扫描并验证case结构
    # 4. 返回数据集信息
    pass

@router.get("/datasets")
async def list_datasets():
    """获取所有数据集列表"""
    # 扫描 datasets/ 目录
    # 返回数据集列表（名称、case数量、创建时间等）
    pass

@router.get("/datasets/{dataset_name}")
async def get_dataset_info(dataset_name: str):
    """获取数据集详细信息"""
    # 返回包含的case列表
    # 每个case的文件状态
    pass

@router.delete("/datasets/{dataset_name}")
async def delete_dataset(dataset_name: str):
    """删除数据集"""
    pass

# ========== 批量执行 ==========

@router.post("/execute")
async def create_batch_task(
    dataset_name: str = Form(...),
    selected_cases: Optional[str] = Form(None)  # JSON数组
):
    """创建批量执行任务

    注意：
    - 按顺序逐个执行case，每次只处理1个
    - 每次执行都会重新生成步骤1输出
    """
    # 1. 验证数据集存在
    # 2. 创建任务记录
    # 3. 启动后台处理
    # 4. 返回任务ID
    pass

@router.get("/tasks/{task_id}")
async def get_batch_task_status(task_id: str):
    """获取批量任务状态"""
    # 返回任务进度、统计、每个case的状态
    pass

@router.get("/tasks")
async def list_batch_tasks(limit: int = 20):
    """获取批量任务历史"""
    # 返回最近的批量执行任务列表
    pass

@router.post("/tasks/{task_id}/cancel")
async def cancel_batch_task(task_id: str):
    """取消正在执行的批量任务"""
    pass

# ========== 结果下载 ==========

@router.get("/tasks/{task_id}/results")
async def download_batch_results(task_id: str):
    """下载批量执行结果（ZIP打包）"""
    # 打包所有生成的JSON和MD文件
    # 返回ZIP文件
    pass

@router.get("/tasks/{task_id}/report")
async def download_batch_report(task_id: str):
    """下载批量执行报告（JSON）"""
    pass

@router.get("/tasks/{task_id}/cases/{case_name}/report")
async def download_case_report(
    task_id: str,
    case_name: str,
    file_type: str  # json | md
):
    """下载单个case的输出文件"""
    pass

# ========== WebSocket ==========

@router.websocket("/ws/{task_id}")
async def batch_task_websocket(websocket: WebSocket, task_id: str):
    """WebSocket连接，实时推送任务进度"""
    await websocket.accept()
    # 推送进度更新
    # 推送case状态变化
    # 推送完成通知
    pass
```

### 3.2 核心服务实现

```python
# backend/app/services/batch_processor.py

from pathlib import Path
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor
from app.models.batch import BatchTask, CaseResult
from app.models.task import create_task, update_task
import logging

logger = logging.getLogger(__name__)


class WebBatchProcessor:
    """Web版批量处理器"""

    def __init__(self, datasets_dir: Path):
        self.datasets_dir = datasets_dir
        self.active_tasks: Dict[str, BatchTask] = {}

    async def create_task(
        self,
        dataset_name: str,
        selected_cases: List[str] = None
    ) -> BatchTask:
        """创建批量任务

        注意：
        - 按顺序逐个执行case，每次只处理1个
        - 每次执行都会重新生成步骤1输出
        """
        # 1. 验证数据集
        dataset_path = self.datasets_dir / dataset_name
        if not dataset_path.exists():
            raise ValueError(f"数据集不存在: {dataset_name}")

        # 2. 扫描cases
        all_cases = self._discover_cases(dataset_path)
        if selected_cases:
            all_cases = [c for c in all_cases if c.name in selected_cases]

        # 3. 创建任务记录
        task = BatchTask(
            task_id=self._generate_task_id(),
            dataset_name=dataset_name,
            mode=mode,
            workers=workers,
            total_cases=len(all_cases),
            cases=[CaseResult(case_name=c.name) for c in all_cases]
        )

        self.active_tasks[task.task_id] = task

        # 4. 启动后台处理
        await self._process_batch(task)

        return task

    def _discover_cases(self, dataset_path: Path) -> List[Path]:
        """扫描数据集目录，发现所有case"""
        cases = []
        for item in dataset_path.iterdir():
            if item.is_dir() and not item.name.startswith('_'):
                cases.append(item)
        return sorted(cases)

    async def _process_batch(self, task: BatchTask):
        """执行批量处理（串行，逐个执行）"""
        from app.services.case_processor import CaseProcessor

        try:
            update_task(
                task.task_id,
                status="processing",
                current_step="开始批量处理..."
            )

            # 串行处理，逐个执行case
            total = len(task.cases)
            for i, case_result in enumerate(task.cases):
                case_path = self.datasets_dir / task.dataset_name / case_result.case_name
                processor = CaseProcessor(str(case_path), {})

                # 更新当前处理进度
                update_task(
                    task.task_id,
                    current_step=f"正在处理 {case_result.case_name} ({i+1}/{total})..."
                )

                # 执行单个case
                result = processor.process()

                # 更新case状态
                case_result.status = result["status"]
                        case_result.step1_output = result.get("step1_output")
                        case_result.step2_output = result.get("step2_output")
                        case_result.error = result.get("error")

                        # 更新任务进度
                        progress = int((i + 1) / len(task.cases) * 100)
                        success_count = sum(1 for c in task.cases if c.status == "success")
                        failed_count = sum(1 for c in task.cases if c.status == "failed")

                        update_task(
                            task.task_id,
                            progress=progress,
                            current_step=f"正在处理 {case_result.case_name}...",
                            result={
                                "success": success_count,
                                "failed": failed_count,
                                "total": len(task.cases)
                            }
                        )

                        # WebSocket推送进度
                        await self._notify_progress(task.task_id, {
                            "case": case_result.case_name,
                            "status": case_result.status,
                            "progress": progress,
                            "success": success_count,
                            "failed": failed_count
                        })

                    except Exception as e:
                        case_result.status = "failed"
                        case_result.error = str(e)
                        logger.error(f"Case {case_result.case_name} 处理失败: {e}")

            # 任务完成
            update_task(
                task.task_id,
                status="completed",
                progress=100,
                current_step="批量处理完成"
            )

        except Exception as e:
            update_task(
                task.task_id,
                status="failed",
                current_step=f"批量处理失败: {str(e)}",
                error=str(e)
            )

    async def _notify_progress(self, task_id: str, progress_data: dict):
        """WebSocket推送进度更新"""
        # TODO: 实现WebSocket推送
        pass

    def _generate_task_id(self) -> str:
        """生成任务ID"""
        import uuid
        return str(uuid.uuid4())
```

### 3.3 数据模型

```python
# backend/app/models/batch.py

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class CaseResult(BaseModel):
    """单个case的处理结果"""
    case_name: str
    status: str = "pending"  # pending | processing | success | failed
    step1_output: Optional[str] = None
    step2_output: Optional[str] = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class BatchTask(BaseModel):
    """批量任务"""
    task_id: str
    dataset_name: str
    total_cases: int
    cases: List[CaseResult]
    status: str = "pending"  # pending | processing | completed | failed
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


class DatasetInfo(BaseModel):
    """数据集信息"""
    name: str
    case_count: int
    created_at: datetime
    size_mb: float
    cases: List[str]  # case名称列表
```

---

## 四、前端页面实现

### 4.1 页面组件结构

```vue
<!-- frontend/src/views/BatchExecution.vue -->
<template>
  <div class="batch-execution">
    <el-page-header @back="goBack" title="返回" content="批量执行" />

    <el-card class="step-card">
      <!-- 步骤指示器 -->
      <el-steps :active="currentStep" finish-status="success">
        <el-step title="选择数据集" description="上传或选择已有数据集" />
        <el-step title="配置参数" description="设置执行参数" />
        <el-step title="查看结果" description="查看执行结果和报告" />
      </el-steps>
    </el-card>

    <!-- 步骤1: 数据集选择 -->
    <el-card v-show="currentStep === 0" class="step-content">
      <template #header>
        <div class="card-header">
          <span>📁 选择数据集</span>
          <el-button type="primary" @click="showUploadDialog = true">
            上传新数据集
          </el-button>
        </div>
      </template>

      <!-- 数据集列表 -->
      <el-radio-group v-model="selectedDataset" class="dataset-list">
        <el-radio
          v-for="dataset in datasets"
          :key="dataset.name"
          :label="dataset.name"
          border
          class="dataset-item"
        >
          <div class="dataset-info">
            <div class="dataset-name">{{ dataset.name }}</div>
            <div class="dataset-meta">
              {{ dataset.case_count }} 个case •
              {{ formatDate(dataset.created_at) }} •
              {{ dataset.size_mb }} MB
            </div>
          </div>
        </el-radio>
      </el-radio-group>

      <div class="step-actions">
        <el-button
          type="primary"
          :disabled="!selectedDataset"
          @click="currentStep = 1"
        >
          下一步
        </el-button>
      </div>
    </el-card>

    <!-- 步骤2: 配置参数 -->
    <el-card v-show="currentStep === 1" class="step-content">
      <template #header>
        <span>⚙️ 配置执行参数</span>
      </template>

      <el-form :model="config" label-width="120px">
        <el-form-item label="筛选Cases">
          <el-select
            v-model="config.selectedCases"
            multiple
            filterable
            placeholder="默认处理所有case（可选）"
            style="width: 100%"
          >
            <el-option
              v-for="case in datasetCases"
              :key="case"
              :label="case"
              :value="case"
            />
          </el-select>
        </el-form-item>
      </el-form>

      <div class="step-actions">
        <el-button @click="currentStep = 0">上一步</el-button>
        <el-button type="primary" @click="startExecution">
          开始执行
        </el-button>
      </div>
    </el-card>

    <!-- 步骤3: 查看结果 -->
    <el-card v-show="currentStep === 2" class="step-content">
      <template #header>
        <span>📊 执行结果</span>
      </template>

      <!-- 执行进度 -->
      <div v-if="taskStatus.status === 'processing'" class="progress-section">
        <el-progress
          :percentage="taskStatus.progress"
          :status="taskStatus.failed > 0 ? 'exception' : undefined"
        />
        <div class="progress-info">
          {{ taskStatus.current_step }}
        </div>
        <div class="progress-stats">
          <el-tag type="success">成功: {{ taskStatus.success }}</el-tag>
          <el-tag type="danger">失败: {{ taskStatus.failed }}</el-tag>
          <el-tag>总计: {{ taskStatus.total }}</el-tag>
        </div>
      </div>

      <!-- 统计汇总 -->
      <div class="summary-section">
        <el-row :gutter="16">
          <el-col :span="6">
            <el-statistic title="总计" :value="taskStatus.total" />
          </el-col>
          <el-col :span="6">
            <el-statistic
              title="成功"
              :value="taskStatus.success"
              class="success"
            />
          </el-col>
          <el-col :span="6">
            <el-statistic
              title="失败"
              :value="taskStatus.failed"
              class="failed"
            />
          </el-col>
          <el-col :span="6">
            <el-statistic title="耗时" :value="duration" suffix="秒" />
          </el-col>
        </el-row>
      </div>

      <!-- Case结果列表 -->
      <el-table :data="caseResults" stripe>
        <el-table-column prop="case_name" label="Case ID" width="150" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="步骤1" width="150">
          <template #default="{ row }">
            <el-icon v-if="row.step1_output" color="#67C23A">
              <CircleCheck />
            </el-icon>
            <span>{{ row.step1_output || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="step2_output" label="步骤2" />
        <el-table-column prop="error" label="错误信息" show-overflow-tooltip />
      </el-table>

      <!-- 操作按钮 -->
      <div class="result-actions">
        <el-button type="primary" @click="downloadAllResults">
          下载所有结果
        </el-button>
        <el-button @click="downloadReport">导出报告</el-button>
        <el-button @click="reset">重新执行</el-button>
      </div>
    </el-card>

    <!-- 上传对话框 -->
    <el-dialog v-model="showUploadDialog" title="上传数据集" width="500px">
      <el-upload
        drag
        action="/api/v1/batch/datasets/upload"
        accept=".zip"
        :on-success="handleUploadSuccess"
        :on-error="handleUploadError"
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          拖拽ZIP文件到此处或<em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            请上传包含case文件夹的ZIP压缩包
          </div>
        </template>
      </el-upload>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const router = useRouter()

// 状态管理
const currentStep = ref(0)
const selectedDataset = ref('')
const datasets = ref([])
const datasetCases = ref([])
const showUploadDialog = ref(false)

const config = ref({
  selectedCases: []
})

const taskStatus = ref({
  task_id: '',
  status: 'pending',
  progress: 0,
  current_step: '',
  success: 0,
  failed: 0,
  total: 0
})

const caseResults = ref([])
const startTime = ref(0)
const duration = ref(0)

// WebSocket连接
let ws: WebSocket | null = null

// 计算属性
const getStatusType = (status: string) => {
  const map = {
    success: 'success',
    failed: 'danger',
    processing: 'warning',
    pending: 'info'
  }
  return map[status] || 'info'
}

const getStatusText = (status: string) => {
  const map = {
    success: '成功',
    failed: '失败',
    processing: '处理中',
    pending: '等待'
  }
  return map[status] || status
}

// 加载数据集列表
const loadDatasets = async () => {
  try {
    const { data } = await axios.get('/api/v1/batch/datasets')
    datasets.value = data.data
  } catch (error) {
    ElMessage.error('加载数据集失败')
  }
}

// 监听数据集选择
watch(selectedDataset, async (newVal) => {
  if (newVal) {
    try {
      const { data } = await axios.get(`/api/v1/batch/datasets/${newVal}`)
      datasetCases.value = data.data.cases
    } catch (error) {
      ElMessage.error('加载case列表失败')
    }
  }
})

// 开始执行
const startExecution = async () => {
  try {
    const formData = new FormData()
    formData.append('dataset_name', selectedDataset.value)
    formData.append('mode', config.value.mode)
    formData.append('workers', config.value.workers.toString())
    if (config.value.selectedCases.length > 0) {
      formData.append('selected_cases', JSON.stringify(config.value.selectedCases))
    }

    const { data } = await axios.post('/api/v1/batch/execute', formData)

    taskStatus.value = data.data
    currentStep.value = 2
    startTime.value = Date.now()

    // 连接WebSocket
    connectWebSocket(data.data.task_id)

    // 开始轮询任务状态
    startPolling(data.data.task_id)

  } catch (error) {
    ElMessage.error('启动批量执行失败')
  }
}

// WebSocket连接
const connectWebSocket = (taskId: string) => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsUrl = `${protocol}//${window.location.host}/api/v1/batch/ws/${taskId}`

  ws = new WebSocket(wsUrl)

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data)
    // 更新进度
    if (data.type === 'progress') {
      taskStatus.value.progress = data.progress
      taskStatus.value.current_step = data.current_step
      taskStatus.value.success = data.success
      taskStatus.value.failed = data.failed
    }
    // 更新case状态
    else if (data.type === 'case_update') {
      const index = caseResults.value.findIndex(c => c.case_name === data.case)
      if (index !== -1) {
        caseResults.value[index] = { ...caseResults.value[index], ...data }
      }
    }
  }

  ws.onerror = () => {
    ElMessage.error('WebSocket连接失败，将使用轮询方式更新进度')
  }
}

// 轮询任务状态
const pollTimer = ref(null)
const startPolling = (taskId: string) => {
  pollTimer.value = setInterval(async () => {
    try {
      const { data } = await axios.get(`/api/v1/batch/tasks/${taskId}`)
      taskStatus.value = data.data
      caseResults.value = data.data.cases

      // 更新耗时
      if (taskStatus.value.status === 'completed') {
        duration.value = Math.round((Date.now() - startTime.value) / 1000)
        stopPolling()
        ElMessage.success('批量执行完成！')
      }
    } catch (error) {
      console.error('轮询任务状态失败', error)
    }
  }, 2000)
}

const stopPolling = () => {
  if (pollTimer.value) {
    clearInterval(pollTimer.value)
    pollTimer.value = null
  }
  if (ws) {
    ws.close()
    ws = null
  }
}

// 下载所有结果
const downloadAllResults = () => {
  window.open(`/api/v1/batch/tasks/${taskStatus.value.task_id}/results`)
}

// 下载报告
const downloadReport = () => {
  window.open(`/api/v1/batch/tasks/${taskStatus.value.task_id}/report`)
}

// 重置
const reset = () => {
  currentStep.value = 0
  taskStatus.value = {
    task_id: '',
    status: 'pending',
    progress: 0,
    current_step: '',
    success: 0,
    failed: 0,
    total: 0
  }
  caseResults.value = []
}

// 上传成功
const handleUploadSuccess = (response: any) => {
  ElMessage.success('数据集上传成功')
  showUploadDialog.value = false
  loadDatasets()
}

// 上传失败
const handleUploadError = () => {
  ElMessage.error('数据集上传失败')
}

// 格式化日期
const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

const goBack = () => {
  router.push('/')
}

onMounted(() => {
  loadDatasets()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.batch-execution {
  padding: 20px;
}

.step-card {
  margin-bottom: 20px;
}

.step-content {
  min-height: 400px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dataset-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 100%;
}

.dataset-item {
  width: 100%;
  padding: 16px;
}

.dataset-info {
  margin-left: 12px;
}

.dataset-name {
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 4px;
}

.dataset-meta {
  font-size: 13px;
  color: #909399;
}

.step-actions {
  margin-top: 24px;
  text-align: right;
}

.radio-desc {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.hint {
  font-size: 12px;
  color: #909399;
  margin-left: 12px;
}

.progress-section {
  margin-bottom: 24px;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 4px;
}

.progress-info {
  margin-top: 12px;
  font-size: 14px;
  color: #606266;
}

.progress-stats {
  margin-top: 12px;
  display: flex;
  gap: 8px;
}

.summary-section {
  margin-bottom: 24px;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 4px;
}

.summary-section :deep(.success) {
  color: #67C23A;
}

.summary-section :deep(.failed) {
  color: #F56C6C;
}

.result-actions {
  margin-top: 24px;
  display: flex;
  gap: 12px;
}
</style>
```

---

## 五、文件预览功能 ⭐

### 5.1 功能概述

**核心特性**：
- 👁️ **在线预览**：无需下载，直接在浏览器中查看文件内容
- 📄 **Markdown渲染**：MD报告实时渲染，支持代码高亮
- 🎨 **JSON格式化**：JSON文件自动格式化，语法高亮
- 🔍 **全文搜索**：在预览内容中快速搜索关键字
- 📎 **快速定位**：点击case名称直接跳转到对应内容
- 📱 **响应式设计**：支持移动端预览

### 5.2 预览界面设计

#### 5.2.1 Case结果详情页

```
┌──────────────────────────────────────────────────────────┐
│  ← 返回    case_001 - 执行结果详情                        │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ┌────────────────────────────────────────────────┐      │
│  │  状态: ✅ 成功    耗时: 2分15秒                  │      │
│  └────────────────────────────────────────────────┘      │
│                                                          │
│  ┌────────────────────────────────────────────────┐      │
│  │  📄 步骤1输出 (JSON)                            │      │
│  │  ┌──────────────────────────────────────────┐  │      │
│  │  │ {                                        │  │      │
│  │  │   "case_name": "case_001",               │  │      │
│  │  │   "check_point_data": {                  │  │      │
│  │  │     "检查点1": {                          │  │      │
│  │  │       "id": "001",                        │  │      │
│  │  │       "value": "..."                      │  │      │
│  │  │     }                                     │  │      │
│  │  │   }                                       │  │      │
│  │  │ }                                        │  │      │
│  │  └──────────────────────────────────────────┘  │      │
│  │                                                │      │
│  │  [📥 下载JSON] [📋 复制内容] [🔍 搜索]        │      │
│  └────────────────────────────────────────────────┘      │
│                                                          │
│  ┌────────────────────────────────────────────────┐      │
│  │  📋 步骤2输出 (Markdown报告)                    │      │
│  │  ┌──────────────────────────────────────────┐  │      │
│  │  │ # case_001 验证报告                       │  │      │
│  │  │                                          │  │      │
│  │  │ ## 验证结果汇总                           │  │      │
│  │  │ - 总检查点数: 50                          │  │      │
│  │  │ - 匹配成功: 48                            │  │      │
│  │  │ - 匹配失败: 2                             │  │      │
│  │  │                                          │  │      │
│  │  │ ## 详细匹配结果                           │  │      │
│  │  │ | 检查点 | 状态 | 置信度 |              │  │      │
│  │  │ |--------|------|--------|              │  │      │
│  │  │ ...                                      │  │      │
│  │  └──────────────────────────────────────────┘  │      │
│  │                                                │      │
│  │  [📥 下载MD] [📋 复制内容] [🔍 搜索] [🖨️ 打印] │      │
│  └────────────────────────────────────────────────┘      │
│                                                          │
│  ┌────────────────────────────────────────────────┐      │
│  │  🔄 快速操作                                   │      │
│  │  [重新执行此case] [导出为PDF] [分享链接]       │      │
│  └────────────────────────────────────────────────┘      │
└──────────────────────────────────────────────────────────┘
```

### 5.3 后端API实现

```python
# backend/app/api/v1/batch.py

@router.get("/tasks/{task_id}/cases/{case_name}/preview")
async def preview_case_file(
    task_id: str,
    case_name: str,
    file_type: str  # json | md
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
    # 1. 根据task_id获取任务信息
    task = get_task(task_id)

    # 2. 构建文件路径
    dataset_path = get_dataset_path(task.dataset_name)
    case_path = dataset_path / case_name

    # 3. 查找目标文件
    if file_type == "json":
        file_pattern = f"{case_name}_check_point_*.json"
    else:  # md
        file_pattern = f"{case_name}_validation_report_*.md"

    files = list(case_path.glob(file_pattern))
    if not files:
        raise HTTPException(status_code=404, detail="文件不存在")

    # 取最新文件
    latest_file = sorted(files, key=lambda f: f.stat().st_mtime, reverse=True)[0]

    # 4. 读取文件内容
    with open(latest_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 5. 返回内容
    return {
        "content": content,
        "size": latest_file.stat().st_size,
        "lines": content.count('\n') + 1,
        "filename": latest_file.name,
        "encoding": "utf-8"
    }
```

### 5.4 前端组件使用

```vue
<template>
  <!-- 在结果列表中点击case名称打开预览 -->
  <el-table :data="caseResults">
    <el-table-column prop="case_name" label="Case ID">
      <template #default="{ row }">
        <el-link
          v-if="row.status === 'success'"
          @click="openPreview(row)"
          type="primary"
        >
          {{ row.case_name }}
        </el-link>
        <span v-else>{{ row.case_name }}</span>
      </template>
    </el-table-column>
  </el-table>

  <!-- 文件预览对话框 -->
  <FilePreview
    v-model="previewVisible"
    :task-id="taskId"
    :case-name="selectedCase"
    file-type="md"
  />
</template>
```

### 5.5 预览功能特性

#### 5.5.1 JSON预览

- ✅ 语法高亮（使用highlight.js）
- ✅ 自动格式化缩进
- ✅ 错误处理
- ✅ 复制/下载

#### 5.5.2 Markdown预览

- ✅ 实时渲染（marked.js）
- ✅ 代码高亮
- ✅ 表格渲染
- ✅ 打印支持

---

## 六、部署和使用

### 5.1 启动服务

```bash
# 使用现有启动脚本
start.bat  # Windows
./start.sh # Linux/Mac

# 或手动启动
cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
cd frontend && npm run dev
```

### 5.2 访问页面

```
http://localhost:5173/batch
```

### 5.3 准备测试数据集

**数据集目录结构**：
```
datasets/
├── dataset_001/              # 数据集名称（任意命名）
│   ├── case_001/            # case目录（任意命名）
│   │   ├── 招标文件.pdf      # 招标文件（支持PDF/DOCX）
│   │   ├── 投标文件.pdf      # 投标文件（支持PDF/DOCX）
│   │   └── 人工标注.xlsx    # 人工标注的检查点Excel
│   ├── case_002/
│   │   ├── zb.pdf            # 或使用简写命名
│   │   ├── tb.pdf
│   │   └── manual.xlsx
│   └── case_003/
│       ├── 招标文件.docx     # 支持DOCX格式
│       ├── 投标文件.docx
│       └── 标注.xlsx
└── dataset_002/
    └── ...
```

**支持的文件格式**：

| 文件类型 | 支持格式 | 识别规则 |
|---------|---------|---------|
| 招标文件 | `.pdf`, `.docx` | `*招标*.pdf/.docx` → `*zb*.pdf/.docx` → 第1个`.pdf/.docx` |
| 投标文件 | `.pdf`, `.docx` | `*投标*.pdf/.docx` → `*tb*.pdf/.docx` → 第2个`.pdf/.docx` |
| 标注文件 | `.xlsx`, `.xls` | 第1个`.xlsx`或`.xls`文件 |

**处理流程**：

```
步骤1: 文档提取 (PDF/DOCX → JSON)
  ├─ 调用后端API提取检查点
  └─ 生成: *_check_point_*.json

步骤2: LLM验证 (Excel + JSON → MD报告)
  ├─ 使用智谱AI进行语义匹配
  └─ 生成: *_validation_report_*.md
```

**打包为ZIP**：
```bash
# 在datasets目录下
zip -r dataset_001.zip dataset_001/
```

### 5.4 使用流程

1. **上传数据集**：点击"上传新数据集"按钮，上传ZIP文件
2. **选择数据集**：从列表中选择要执行的数据集
3. **配置参数**（可选）：
   - 筛选特定case（默认执行全部）
4. **开始执行**：点击"开始执行"按钮
5. **查看进度**：实时查看处理进度和每个case的状态（按顺序逐个执行）
6. **下载结果**：执行完成后下载所有生成的文件

---

## 六、功能扩展

### 6.1 高级功能

- **定时任务**：设置定时批量执行
- **任务通知**：执行完成后发送邮件/钉钉通知
- **结果对比**：对比不同批次执行结果
- **性能分析**：生成执行时间、成功率等统计图表

### 6.2 权限控制

- 用户登录认证
- 数据集访问权限
- 任务执行权限

### 6.3 多数据集支持

- 同时选择多个数据集执行
- 数据集分组管理
- 数据集版本控制

---

这个Web版批量执行方案提供了完整的用户界面和API实现，可以让非技术人员轻松地批量执行测试用例，实时查看进度并下载结果。
