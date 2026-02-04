<template>
  <div class="processing-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <h2>验证处理中</h2>
          <el-tag v-if="task" :type="getStatusType(task.status)">
            {{ getStatusText(task.status) }}
          </el-tag>
        </div>
      </template>

      <div v-if="task" class="progress-content">
        <!-- 进度条 -->
        <el-progress
          :percentage="taskProgress"
          :status="getProgressStatus(task.status)"
          :stroke-width="20"
        />

        <!-- 当前步骤 -->
        <div class="current-step">
          <el-icon class="step-icon"><Loading /></el-icon>
          <span>{{ currentStep }}</span>
        </div>

        <!-- 任务信息 -->
        <el-descriptions :column="2" border class="task-info">
          <el-descriptions-item label="任务ID">
            {{ task.task_id }}
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">
            {{ formatTime(task.created_at) }}
          </el-descriptions-item>
        </el-descriptions>

        <!-- 完成后的操作 -->
        <div v-if="task.status === 'completed'" class="actions">
          <el-button type="primary" size="large" @click="viewReport">
            <el-icon class="el-icon--left"><Document /></el-icon>
            查看报告
          </el-button>
          <el-button type="success" size="large" @click="downloadReport">
            <el-icon class="el-icon--left"><Download /></el-icon>
            下载报告
          </el-button>
        </div>

        <!-- 失败时的提示 -->
        <el-alert
          v-if="task.status === 'failed'"
          title="验证失败"
          type="error"
          :description="task.error || '未知错误'"
          :closable="false"
          show-icon
        />
      </div>

      <el-skeleton v-else :rows="5" animated />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Loading, Document, Download } from '@element-plus/icons-vue'
import { useTaskStore } from '@/stores/task'
import type { Task, TaskStatus } from '@/types'

const router = useRouter()
const route = useRoute()
const taskStore = useTaskStore()

const task = ref<Task | null>(null)
const refreshTimer = ref<number | null>(null)

const taskProgress = computed(() => task.value?.progress || 0)
const currentStep = computed(() => task.value?.current_step || '初始化中...')

onMounted(async () => {
  const taskId = route.params.taskId as string

  // 初始加载任务信息
  try {
    await taskStore.refreshTask(taskId)
    task.value = taskStore.currentTask

    // 如果任务已完成，停止轮询
    if (task.value?.status === 'completed' || task.value?.status === 'failed') {
      return
    }

    // 定时刷新任务状态
    refreshTimer.value = window.setInterval(async () => {
      await taskStore.refreshTask(taskId)
      task.value = taskStore.currentTask

      // 任务完成或失败时停止轮询
      if (task.value?.status === 'completed' || task.value?.status === 'failed') {
        if (refreshTimer.value) {
          clearInterval(refreshTimer.value)
        }
      }
    }, 2000)

  } catch (error: any) {
    ElMessage.error(`加载任务失败: ${error.message}`)
    router.push('/')
  }
})

onUnmounted(() => {
  if (refreshTimer.value) {
    clearInterval(refreshTimer.value)
  }
})

function getStatusType(status: TaskStatus) {
  const types = {
    pending: 'info',
    processing: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return types[status] || 'info'
}

function getStatusText(status: TaskStatus) {
  const texts = {
    pending: '等待中',
    processing: '处理中',
    completed: '已完成',
    failed: '失败'
  }
  return texts[status] || status
}

function getProgressStatus(status: TaskStatus) {
  if (status === 'completed') return 'success'
  if (status === 'failed') return 'exception'
  return undefined
}

function formatTime(timeStr: string) {
  const date = new Date(timeStr)
  return date.toLocaleString('zh-CN')
}

function viewReport() {
  if (task.value) {
    router.push(`/report/${task.value.task_id}`)
  }
}

function downloadReport() {
  if (task.value) {
    // 直接下载报告文件
    window.location.href = `/api/v1/reports/${task.value.task_id}`
    ElMessage.success('下载已开始')
  }
}
</script>

<style scoped>
.processing-container {
  max-width: 800px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-header h2 {
  margin: 0;
  font-size: 20px;
}

.progress-content {
  padding: 20px 0;
}

.current-step {
  margin-top: 20px;
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  color: #606266;
}

.step-icon {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.task-info {
  margin-top: 30px;
}

.actions {
  margin-top: 30px;
  display: flex;
  justify-content: center;
  gap: 15px;
}
</style>
