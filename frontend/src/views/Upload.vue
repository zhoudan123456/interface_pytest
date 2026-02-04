<template>
  <div class="upload-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <el-button @click="goBack" circle>
            <el-icon><ArrowLeft /></el-icon>
          </el-button>
          <h2>文件上传 - 两步验证流程</h2>
        </div>
      </template>

      <el-alert
        title="验证流程说明"
        type="info"
        :closable="false"
        style="margin-bottom: 20px"
      >
        <div class="flow-description">
          <p><strong>步骤1（独立）：</strong>上传招标文件(PDF)或投标文件(PDF)，调用后端API提取检查点。两个文件都需要上传。</p>
          <p><strong>步骤2（独立）：</strong>上传Excel标注和JSON算法结果，使用AI进行语义匹配验证。可直接进行，无需等待步骤1</p>
        </div>
      </el-alert>

      <el-tabs v-model="activeTab" type="border-card">
        <!-- 步骤1: PDF上传 -->
        <el-tab-pane label="步骤1: API提取" name="step1">
          <el-form :model="pdfForm" label-width="140px">
            <el-form-item label="招标文件(PDF)">
              <FileUploader
                file-type="pdf"
                @uploaded="handleZbPdfUpload"
              />
              <div v-if="pdfForm.zbPdfFileId" class="file-info">
                <el-icon><SuccessFilled /></el-icon>
                <span>{{ pdfForm.zbPdfFileName }}</span>
              </div>
            </el-form-item>

            <el-form-item label="投标文件(PDF)">
              <FileUploader
                file-type="pdf"
                @uploaded="handleTbPdfUpload"
              />
              <div v-if="pdfForm.tbPdfFileId" class="file-info">
                <el-icon><SuccessFilled /></el-icon>
                <span>{{ pdfForm.tbPdfFileName }}</span>
              </div>
            </el-form-item>

            <el-form-item>
              <el-button
                type="primary"
                size="large"
                :loading="apiExtracting"
                :disabled="!canExtract"
                @click="startApiExtraction"
              >
                <el-icon class="el-icon--left"><MagicStick /></el-icon>
                提取检查点
              </el-button>
            </el-form-item>

            <!-- 生成的文件下载区域 -->
            <el-form-item v-if="extractionFiles.length > 0" label="生成的文件">
              <el-card class="files-card">
                <template #header>
                  <div class="files-header">
                    <span>步骤1生成的JSON文件（可下载）</span>
                    <el-button size="small" @click="refreshFileList">
                      <el-icon><Refresh /></el-icon>
                      刷新
                    </el-button>
                  </div>
                </template>
                <div class="files-list">
                  <div v-for="file in extractionFiles" :key="file.filename" class="file-item">
                    <div class="file-item-info">
                      <el-icon><Document /></el-icon>
                      <div class="file-details">
                        <div class="file-name">{{ file.filename }}</div>
                        <div class="file-meta">
                          {{ file.type === 'check_point' ? '检查点数据' : '招标信息' }} |
                          {{ formatFileSize(file.size) }} |
                          {{ formatTime(file.modified_time) }}
                        </div>
                      </div>
                    </div>
                    <el-button type="primary" size="small" @click="downloadFile(file.filename)">
                      <el-icon><Download /></el-icon>
                      下载
                    </el-button>
                  </div>
                </div>
              </el-card>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- 步骤2: LLM验证 -->
        <el-tab-pane label="步骤2: LLM验证" name="step2">
          <el-form :model="form" label-width="120px">
            <!-- Excel文件上传 -->
            <el-form-item label="Excel标注文件" required>
              <FileUploader
                file-type="excel"
                @uploaded="handleExcelUpload"
              />
              <div v-if="form.excelFileId" class="file-info">
                <el-icon><SuccessFilled /></el-icon>
                <span>{{ form.excelFileName }}</span>
              </div>
            </el-form-item>

            <!-- JSON文件上传 -->
            <el-form-item label="JSON算法结果" required>
              <FileUploader
                file-type="json"
                @uploaded="handleJsonUpload"
              />
              <div v-if="form.jsonFileId" class="file-info">
                <el-icon><SuccessFilled /></el-icon>
                <span>{{ form.jsonFileName }}</span>
              </div>
            </el-form-item>

            <!-- 提交按钮 -->
            <el-form-item>
              <el-button
                type="primary"
                size="large"
                :loading="taskStore.isLoading"
                :disabled="!canSubmit"
                @click="startValidation"
              >
                <el-icon class="el-icon--left"><MagicStick /></el-icon>
                开始验证
              </el-button>
            </el-form-item>

            <!-- 生成的文件下载区域 -->
            <el-form-item v-if="reportFiles.length > 0" label="生成的文件">
              <el-card class="files-card">
                <template #header>
                  <div class="files-header">
                    <span>步骤2生成的验证报告（可下载）</span>
                    <el-button size="small" @click="refreshReportList">
                      <el-icon><Refresh /></el-icon>
                      刷新
                    </el-button>
                  </div>
                </template>
                <div class="files-list">
                  <div v-for="file in reportFiles" :key="file.filename" class="file-item">
                    <div class="file-item-info">
                      <el-icon><Document /></el-icon>
                      <div class="file-details">
                        <div class="file-name">{{ file.filename }}</div>
                        <div class="file-meta">
                          验证报告 | {{ formatFileSize(file.size) }} | {{ formatTime(file.modified_time) }}
                        </div>
                      </div>
                    </div>
                    <el-button type="success" size="small" @click="downloadReportFile(file.filename)">
                      <el-icon><Download /></el-icon>
                      下载
                    </el-button>
                  </div>
                </div>
              </el-card>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, MagicStick, SuccessFilled, Document, Download, Refresh } from '@element-plus/icons-vue'
import { useTaskStore } from '@/stores/task'
import FileUploader from '@/components/FileUploader.vue'
import type { FileInfo } from '@/types'
import {
  getExtractionFiles,
  downloadExtractionFile,
  type ExtractFileInfo,
  getReportFiles,
  downloadReportFile as downloadReportFileApi,
  type ReportFileInfo
} from '@/api/upload'
import axios from 'axios'

const router = useRouter()
const taskStore = useTaskStore()

const activeTab = ref('step1')
const apiExtracting = ref(false)
const apiExtracted = ref(false)
const extractionFiles = ref<ExtractFileInfo[]>([])
const reportFiles = ref<ReportFileInfo[]>([])

const pdfForm = ref({
  zbPdfFileId: '',
  zbPdfFileName: '',
  tbPdfFileId: '',
  tbPdfFileName: ''
})

const form = ref({
  excelFileId: '',
  excelFileName: '',
  jsonFileId: '',
  jsonFileName: ''
})

const canExtract = computed(() => {
  return pdfForm.value.zbPdfFileId || pdfForm.value.tbPdfFileId
})

const canSubmit = computed(() => {
  return form.value.excelFileId && form.value.jsonFileId
})

// 监听标签页切换
watch(activeTab, async (newTab) => {
  if (newTab === 'step2') {
    await loadReportFiles()
  }
})

// 页面加载时获取文件列表
onMounted(async () => {
  await loadExtractionFiles()
})

async function loadExtractionFiles() {
  try {
    const response = await getExtractionFiles()
    if (response.code === 200) {
      extractionFiles.value = response.data || []
    }
  } catch (error) {
    // 忽略加载错误，可能还没有文件
  }
}

async function loadReportFiles() {
  try {
    const response = await getReportFiles()
    if (response.code === 200) {
      reportFiles.value = response.data || []
    }
  } catch (error) {
    // 忽略加载错误，可能还没有文件
  }
}

async function refreshFileList() {
  await loadExtractionFiles()
  ElMessage.success('文件列表已刷新')
}

async function refreshReportList() {
  await loadReportFiles()
  ElMessage.success('报告列表已刷新')
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
}

function formatTime(timestamp: number): string {
  const date = new Date(timestamp * 1000)
  return date.toLocaleString('zh-CN')
}

function downloadFile(filename: string) {
  try {
    downloadExtractionFile(filename)
    ElMessage.success('下载已开始')
  } catch (error) {
    ElMessage.error('下载失败')
  }
}

function downloadReportFile(filename: string) {
  try {
    downloadReportFileApi(filename)
    ElMessage.success('下载已开始')
  } catch (error) {
    ElMessage.error('下载失败')
  }
}

function handleZbPdfUpload(fileInfo: FileInfo) {
  pdfForm.value.zbPdfFileId = fileInfo.file_id
  pdfForm.value.zbPdfFileName = fileInfo.filename
  ElMessage.success('招标文件上传成功')
}

function handleTbPdfUpload(fileInfo: FileInfo) {
  pdfForm.value.tbPdfFileId = fileInfo.file_id
  pdfForm.value.tbPdfFileName = fileInfo.filename
  ElMessage.success('投标文件上传成功')
}

function handleExcelUpload(fileInfo: FileInfo) {
  form.value.excelFileId = fileInfo.file_id
  form.value.excelFileName = fileInfo.filename
  ElMessage.success('Excel文件上传成功')
}

function handleJsonUpload(fileInfo: FileInfo) {
  form.value.jsonFileId = fileInfo.file_id
  form.value.jsonFileName = fileInfo.filename
  ElMessage.success('JSON文件上传成功')
}

async function startApiExtraction() {
  if (!canExtract.value) {
    ElMessage.warning('请至少上传招标文件或投标文件')
    return
  }

  // 检查文件上传情况
  const hasZb = !!pdfForm.value.zbPdfFileId
  const hasTb = !!pdfForm.value.tbPdfFileId

  if (!hasZb && !hasTb) {
    ElMessage.warning('请至少上传招标文件或投标文件')
    return
  }

  try {
    apiExtracting.value = true

    // 根据上传的文件显示不同的提示信息
    if (hasZb && hasTb) {
      ElMessage.info('正在调用API提取检查点...')
    } else if (hasZb) {
      ElMessage.info('正在调用API提取招标文件检查点...')
    } else {
      ElMessage.info('正在调用API提取投标文件检查点...')
    }

    // 调用后端API进行PDF处理和检查点提取
    const response = await axios.post('/api/v1/tasks/extract', {
      zb_pdf_file_id: pdfForm.value.zbPdfFileId || '',
      tb_pdf_file_id: pdfForm.value.tbPdfFileId || ''
    })

    if (response.data.code === 200) {
      const successMsg = hasZb && hasTb
        ? '检查点提取成功！结果已保存到 test_data/evaluation/responses/ 目录'
        : '文件处理成功！结果已保存到 test_data/evaluation/responses/ 目录'
      ElMessage.success(successMsg)
      apiExtracted.value = true
      // 刷新文件列表
      await loadExtractionFiles()
    } else {
      ElMessage.error(response.data.message || '提取失败')
    }
  } catch (error: any) {
    ElMessage.error(`API提取失败: ${error.response?.data?.detail || error.response?.data?.message || error.message || '未知错误'}`)
  } finally {
    apiExtracting.value = false
  }
}

async function startValidation() {
  if (!canSubmit.value) {
    ElMessage.warning('请先上传Excel和JSON文件')
    return
  }

  try {
    const task = await taskStore.createTask(
      form.value.excelFileId,
      form.value.jsonFileId
    )

    ElMessage.success('任务创建成功')

    // 刷新报告列表
    await loadReportFiles()

    // 跳转到处理页面
    router.push(`/processing/${task.task_id}`)
  } catch (error: any) {
    ElMessage.error(`创建任务失败: ${error.message || '未知错误'}`)
  }
}

function goBack() {
  router.push('/')
}
</script>

<style scoped>
.upload-container {
  max-width: 900px;
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

.flow-description p {
  margin: 5px 0;
  line-height: 1.8;
}

.file-info {
  margin-top: 10px;
  padding: 10px;
  background-color: #f0f9ff;
  border: 1px solid #b3d8ff;
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #409eff;
}

.files-card {
  width: 100%;
}

.files-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.files-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.file-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background-color: #f5f7fa;
  border-radius: 6px;
  transition: background-color 0.2s;
}

.file-item:hover {
  background-color: #ecf5ff;
}

.file-item-info {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.file-details {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.file-name {
  font-weight: 500;
  color: #303133;
  word-break: break-all;
}

.file-meta {
  font-size: 12px;
  color: #909399;
}
</style>
