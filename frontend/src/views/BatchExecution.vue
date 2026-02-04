<template>
  <div class="batch-execution">
    <el-page-header @back="goBack" title="返回" content="批量执行" />

    <el-card class="step-card">
      <el-steps :active="currentStep" finish-status="success" align-center>
        <el-step title="选择数据集" description="上传或选择已有数据集" />
        <el-step title="配置参数" description="设置执行参数" />
        <el-step title="查看结果" description="查看执行结果和报告" />
      </el-steps>
    </el-card>

    <!-- 步骤1: 数据集选择 -->
    <el-card v-show="currentStep === 0" class="step-content">
      <template #header>
        <div class="card-header">
          <span>选择数据集</span>
          <el-button type="primary" @click="showUploadDialog = true">
            <el-icon><Upload /></el-icon>
            上传新数据集
          </el-button>
        </div>
      </template>

      <el-skeleton v-if="loadingDatasets" :rows="3" animated />

      <el-empty v-else-if="datasets.length === 0" description="暂无数据集，请上传">
        <el-button type="primary" @click="showUploadDialog = true">上传数据集</el-button>
      </el-empty>

      <el-radio-group v-else v-model="selectedDataset" class="dataset-list">
        <el-radio
          v-for="dataset in datasets"
          :key="dataset.name"
          :label="dataset.name"
          border
          class="dataset-item"
        >
          <div class="dataset-info">
            <div class="dataset-name">
              <el-icon><Folder /></el-icon>
              {{ dataset.name }}
            </div>
            <div class="dataset-meta">
              {{ dataset.case_count }} 个case
              <span class="separator">•</span>
              {{ formatDate(dataset.created_at) }}
              <span class="separator">•</span>
              {{ dataset.size_mb }} MB
            </div>
          </div>
        </el-radio>
      </el-radio-group>

      <div class="step-actions">
        <el-button type="primary" :disabled="!selectedDataset" @click="goToStep(1)">
          下一步
        </el-button>
      </div>
    </el-card>

    <!-- 步骤2: 配置参数 -->
    <el-card v-show="currentStep === 1" class="step-content">
      <template #header>
        <span>配置执行参数</span>
      </template>

      <el-form :model="config" label-width="100px">
        <el-form-item label="数据集">
          <el-tag>{{ selectedDataset }}</el-tag>
        </el-form-item>

        <el-form-item label="包含Cases">
          <el-tag v-if="datasetCases.length === 0" type="info">加载中...</el-tag>
          <el-tag v-else>共 {{ datasetCases.length }} 个case</el-tag>
        </el-form-item>

        <el-form-item label="筛选Cases">
          <el-select
            v-model="config.selectedCases"
            multiple
            filterable
            placeholder="留空则处理所有case（可选）"
            style="width: 100%"
            :max-collapse-tags="5"
            collapse-tags
          >
            <el-option
              v-for="c in datasetCases"
              :key="c"
              :label="c"
              :value="c"
            />
          </el-select>
          <div class="hint">留空则处理所有case</div>
        </el-form-item>
      </el-form>

      <div class="step-actions">
        <el-button @click="currentStep = 0">上一步</el-button>
        <el-button type="primary" :loading="starting" @click="startExecution">
          开始执行
        </el-button>
      </div>
    </el-card>

    <!-- 步骤3: 查看结果 -->
    <el-card v-show="currentStep === 2" class="step-content">
      <template #header>
        <span>执行结果</span>
      </template>

      <!-- 执行进度 -->
      <div v-if="taskStatus.status === 'processing'" class="progress-section">
        <el-progress
          :percentage="taskStatus.progress"
          :status="taskStatus.failed > 0 ? 'exception' : undefined"
          :stroke-width="20"
        >
          <template #default="{ percentage }">
            <span class="progress-text">{{ percentage }}% ({{ taskStatus.success + taskStatus.failed }}/{{ taskStatus.total }})</span>
          </template>
        </el-progress>
        <div class="progress-info">
          <el-icon class="is-loading"><Loading /></el-icon>
          {{ taskStatus.current_step || '处理中...' }}
        </div>
        <div class="progress-stats">
          <el-tag type="success">成功: {{ taskStatus.success }}</el-tag>
          <el-tag type="danger" v-if="taskStatus.failed > 0">失败: {{ taskStatus.failed }}</el-tag>
          <el-tag type="info">总计: {{ taskStatus.total }}</el-tag>
        </div>
      </div>

      <!-- 统计汇总 -->
      <div class="summary-section">
        <el-row :gutter="16">
          <el-col :span="6">
            <el-statistic title="总计" :value="taskStatus.total" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="成功" :value="taskStatus.success">
              <template #prefix>
                <el-icon color="#67C23A"><CircleCheck /></el-icon>
              </template>
            </el-statistic>
          </el-col>
          <el-col :span="6">
            <el-statistic title="失败" :value="taskStatus.failed">
              <template #prefix>
                <el-icon color="#F56C6C"><CircleClose /></el-icon>
              </template>
            </el-statistic>
          </el-col>
          <el-col :span="6">
            <el-statistic title="耗时" :value="duration" suffix="秒">
              <template #prefix>
                <el-icon><Timer /></el-icon>
              </template>
            </el-statistic>
          </el-col>
        </el-row>
      </div>

      <!-- Case结果列表 -->
      <div class="table-section">
        <h3>Case执行详情</h3>
        <el-table :data="caseResults" stripe max-height="400">
          <el-table-column prop="case_name" label="Case ID" width="150" />
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="getStatusType(row.status)">
                {{ getStatusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="步骤1输出" width="150">
            <template #default="{ row }">
              <span v-if="row.step1_output" class="file-name">
                <el-icon color="#67C23A"><Document /></el-icon>
                {{ truncateFileName(row.step1_output) }}
              </span>
              <span v-else class="text-placeholder">-</span>
            </template>
          </el-table-column>
          <el-table-column label="步骤2输出" width="150">
            <template #default="{ row }">
              <span v-if="row.step2_output" class="file-name">
                <el-icon color="#67C23A"><Document /></el-icon>
                {{ truncateFileName(row.step2_output) }}
              </span>
              <span v-else class="text-placeholder">-</span>
            </template>
          </el-table-column>
          <el-table-column prop="error" label="错误信息" show-overflow-tooltip />
        </el-table>
      </div>

      <!-- 操作按钮 -->
      <div class="result-actions">
        <el-button
          type="primary"
          :disabled="taskStatus.status !== 'completed'"
          @click="downloadAllResults"
        >
          <el-icon><Download /></el-icon>
          下载所有结果
        </el-button>
        <el-button
          :disabled="taskStatus.status !== 'completed'"
          @click="downloadReport"
        >
          <el-icon><DocumentCopy /></el-icon>
          导出报告
        </el-button>
        <el-button @click="reset">
          <el-icon><Refresh /></el-icon>
          重新执行
        </el-button>
      </div>
    </el-card>

    <!-- 上传对话框 -->
    <el-dialog v-model="showUploadDialog" title="上传数据集" width="500px">
      <el-upload
        drag
        :action="uploadAction"
        accept=".zip"
        :on-success="handleUploadSuccess"
        :on-error="handleUploadError"
        :before-upload="beforeUpload"
        :show-file-list="false"
      >
        <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
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
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Upload,
  Folder,
  Download,
  DocumentCopy,
  Refresh,
  CircleCheck,
  CircleClose,
  Timer,
  Loading,
  Document,
  UploadFilled
} from '@element-plus/icons-vue'
import * as batchApi from '@/api/batch'
import { BatchWebSocket } from '@/api/batchWebSocket'

const router = useRouter()

// 状态管理
const currentStep = ref(0)
const selectedDataset = ref('')
const datasets = ref<batchApi.DatasetInfo[]>([])
const datasetCases = ref<string[]>([])
const showUploadDialog = ref(false)
const loadingDatasets = ref(false)
const starting = ref(false)

const config = ref({
  selectedCases: [] as string[]
})

const taskStatus = ref<batchApi.BatchTask>({
  task_id: '',
  dataset_name: '',
  total_cases: 0,
  cases: [],
  status: 'pending',
  created_at: null,
  started_at: null,
  completed_at: null,
  error: null,
  progress: 0,
  current_step: '',
  success: 0,
  failed: 0
})

const caseResults = ref<batchApi.CaseResult[]>([])
const startTime = ref(0)
const duration = ref(0)
const pollTimer = ref<number | null>(null)

// WebSocket连接
let ws: BatchWebSocket | null = null

// 计算属性
const uploadAction = computed(() => {
  return `/api/v1/batch/datasets/upload`
})

// 方法
const getStatusType = (status: string) => {
  const map: Record<string, any> = {
    success: 'success',
    failed: 'danger',
    processing: 'warning',
    pending: 'info'
  }
  return map[status] || 'info'
}

const getStatusText = (status: string) => {
  const map: Record<string, string> = {
    success: '成功',
    failed: '失败',
    processing: '处理中',
    pending: '等待'
  }
  return map[status] || status
}

const truncateFileName = (filename: string | null) => {
  if (!filename) return '-'
  if (filename.length > 20) {
    return filename.substring(0, 8) + '...' + filename.substring(filename.length - 8)
  }
  return filename
}

const formatDate = (dateStr: string) => {
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}

// 加载数据集列表
const loadDatasets = async () => {
  loadingDatasets.value = true
  try {
    const response = await batchApi.listDatasets()
    datasets.value = response.data || []
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || '加载数据集失败')
  } finally {
    loadingDatasets.value = false
  }
}

// 监听数据集选择
watch(selectedDataset, async (newVal) => {
  if (newVal) {
    try {
      const response = await batchApi.getDataset(newVal)
      datasetCases.value = response.data?.cases || []
    } catch (error: any) {
      ElMessage.error(error.response?.data?.message || '加载case列表失败')
    }
  }
})

const goToStep = (step: number) => {
  currentStep.value = step
}

// 开始执行
const startExecution = async () => {
  starting.value = true
  try {
    const response = await batchApi.createBatchTask({
      dataset_name: selectedDataset.value,
      selected_cases: config.value.selectedCases.length > 0
        ? config.value.selectedCases
        : undefined
    })

    taskStatus.value = response.data
    caseResults.value = response.data.cases || []
    currentStep.value = 2
    startTime.value = Date.now()

    // 连接WebSocket
    connectWebSocket(response.data.task_id)

    // 开始轮询任务状态（作为WebSocket的备用）
    startPolling(response.data.task_id)

  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || '启动批量执行失败')
  } finally {
    starting.value = false
  }
}

// WebSocket连接
const connectWebSocket = (taskId: string) => {
  ws = new BatchWebSocket(taskId)

  ws.onInit((data) => {
    taskStatus.value = data
    caseResults.value = data.cases || []
  })

  ws.onProgress((data) => {
    taskStatus.value.progress = data.progress
    taskStatus.value.current_step = data.current_step
    taskStatus.value.status = data.status as any
    taskStatus.value.success = data.success
    taskStatus.value.failed = data.failed
  })

  ws.onCaseUpdate((data) => {
    const index = caseResults.value.findIndex(c => c.case_name === data.case_name)
    if (index !== -1) {
      caseResults.value[index] = {
        ...caseResults.value[index],
        status: data.status as any,
        step1_output: data.step1_output,
        step2_output: data.step2_output,
        error: data.error
      }
    }
  })

  ws.onComplete((data) => {
    taskStatus.value = data
    caseResults.value = data.cases || []
    duration.value = Math.round((Date.now() - startTime.value) / 1000)
    stopPolling()
    ElMessage.success('批量执行完成！')
  })

  ws.connect()
}

// 轮询任务状态
const startPolling = (taskId: string) => {
  pollTimer.value = window.setInterval(async () => {
    try {
      const response = await batchApi.getBatchTask(taskId)
      taskStatus.value = response.data
      caseResults.value = response.data.cases || []

      // 更新耗时
      duration.value = Math.round((Date.now() - startTime.value) / 1000)

      // 检查是否完成
      if (response.data.status === 'completed' || response.data.status === 'failed') {
        stopPolling()
        if (response.data.status === 'completed') {
          ElMessage.success('批量执行完成！')
        } else {
          ElMessage.error('批量执行失败：' + (response.data.error || '未知错误'))
        }
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
    ws.disconnect()
    ws = null
  }
}

// 下载所有结果
const downloadAllResults = () => {
  window.open(batchApi.downloadBatchResults(taskStatus.value.task_id))
}

// 下载报告
const downloadReport = () => {
  window.open(batchApi.downloadBatchReport(taskStatus.value.task_id))
}

// 重置
const reset = () => {
  stopPolling()
  currentStep.value = 0
  selectedDataset.value = ''
  datasetCases.value = []
  config.value.selectedCases = []
  taskStatus.value = {
    task_id: '',
    dataset_name: '',
    total_cases: 0,
    cases: [],
    status: 'pending',
    created_at: null,
    started_at: null,
    completed_at: null,
    error: null,
    progress: 0,
    current_step: '',
    success: 0,
    failed: 0
  }
  caseResults.value = []
  duration.value = 0
}

// 上传相关
const beforeUpload = (file: File) => {
  const isZip = file.name.endsWith('.zip')
  if (!isZip) {
    ElMessage.error('只能上传ZIP格式文件')
    return false
  }
  const isLt100M = file.size / 1024 / 1024 < 100
  if (!isLt100M) {
    ElMessage.error('文件大小不能超过100MB')
    return false
  }
  return true
}

const handleUploadSuccess = (response: any) => {
  if (response.code === 200) {
    ElMessage.success('数据集上传成功')
    showUploadDialog.value = false
    loadDatasets()
  } else {
    ElMessage.error(response.message || '上传失败')
  }
}

const handleUploadError = () => {
  ElMessage.error('数据集上传失败')
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
  max-width: 1200px;
  margin: 0 auto;
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
  height: auto;
}

.dataset-info {
  margin-left: 12px;
}

.dataset-name {
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.dataset-meta {
  font-size: 13px;
  color: #909399;
}

.separator {
  margin: 0 6px;
}

.step-actions {
  margin-top: 24px;
  text-align: right;
}

.hint {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.progress-section {
  margin-bottom: 24px;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
}

.progress-text {
  font-weight: bold;
}

.progress-info {
  margin-top: 12px;
  font-size: 14px;
  color: #606266;
  display: flex;
  align-items: center;
  gap: 8px;
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
  border-radius: 8px;
}

.table-section {
  margin-bottom: 24px;
}

.table-section h3 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
}

.file-name {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
}

.text-placeholder {
  color: #c0c4cc;
}

.result-actions {
  margin-top: 24px;
  display: flex;
  gap: 12px;
}
</style>
