<template>
  <div class="report-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <el-button @click="goBack" circle>
            <el-icon><ArrowLeft /></el-icon>
          </el-button>
          <h2>验证报告</h2>
        </div>
      </template>

      <div v-if="loading" class="loading-container">
        <el-skeleton :rows="10" animated />
      </div>

      <div v-else-if="reportContent" class="report-content">
        <!-- 报告操作栏 -->
        <div class="report-actions">
          <el-button type="primary" @click="downloadReport">
            <el-icon class="el-icon--left"><Download /></el-icon>
            下载报告
          </el-button>
          <el-button @click="copyReport">
            <el-icon class="el-icon--left"><DocumentCopy /></el-icon>
            复制内容
          </el-button>
        </div>

        <!-- 报告内容 -->
        <div class="markdown-body" v-html="renderedMarkdown"></div>
      </div>

      <el-empty v-else description="报告不存在或加载失败" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Download, DocumentCopy } from '@element-plus/icons-vue'
import { marked } from 'marked'

const router = useRouter()
const route = useRoute()

const loading = ref(true)
const reportContent = ref('')

const renderedMarkdown = computed(() => {
  return marked(reportContent.value)
})

onMounted(async () => {
  const taskId = route.params.taskId as string

  try {
    // 获取报告内容
    const response = await fetch(`/api/v1/reports/${taskId}`)
    if (response.ok) {
      reportContent.value = await response.text()
    } else {
      throw new Error('报告加载失败')
    }
  } catch (error: any) {
    ElMessage.error(`加载报告失败: ${error.message}`)
  } finally {
    loading.value = false
  }
})

function downloadReport() {
  const taskId = route.params.taskId as string
  window.location.href = `/api/v1/reports/${taskId}`
}

async function copyReport() {
  try {
    await navigator.clipboard.writeText(reportContent.value)
    ElMessage.success('报告内容已复制到剪贴板')
  } catch {
    ElMessage.error('复制失败')
  }
}

function goBack() {
  router.push('/')
}
</script>

<style scoped>
.report-container {
  max-width: 1000px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 15px;
}

.card-header h2 {
  margin: 0;
  font-size: 20px;
}

.loading-container {
  padding: 20px;
}

.report-actions {
  margin-bottom: 20px;
  display: flex;
  gap: 10px;
}

.markdown-body {
  line-height: 1.8;
  color: #303133;
}

.markdown-body :deep(h1) {
  font-size: 28px;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 2px solid #ebeef5;
}

.markdown-body :deep(h2) {
  font-size: 24px;
  margin-top: 30px;
  margin-bottom: 15px;
  padding-bottom: 8px;
  border-bottom: 1px solid #ebeef5;
}

.markdown-body :deep(p) {
  margin-bottom: 15px;
}

.markdown-body :deep(code) {
  background-color: #f5f7fa;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
}

.markdown-body :deep(pre) {
  background-color: #282c34;
  color: #abb2bf;
  padding: 15px;
  border-radius: 5px;
  overflow-x: auto;
}

.markdown-body :deep(pre code) {
  background-color: transparent;
  padding: 0;
}

.markdown-body :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 20px 0;
}

.markdown-body :deep(th),
.markdown-body :deep(td) {
  border: 1px solid #ebeef5;
  padding: 10px;
  text-align: left;
}

.markdown-body :deep(th) {
  background-color: #f5f7fa;
  font-weight: bold;
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  padding-left: 20px;
}

.markdown-body :deep(li) {
  margin-bottom: 8px;
}
</style>
