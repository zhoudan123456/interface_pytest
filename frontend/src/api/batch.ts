/**
 * 批量执行API
 */
import apiClient from './index'

export interface DatasetInfo {
  name: string
  case_count: number
  created_at: string
  size_mb: number
  cases: string[]
  path: string
}

export interface CaseResult {
  case_name: string
  status: 'pending' | 'processing' | 'success' | 'failed'
  step1_output: string | null
  step2_output: string | null
  error: string | null
  start_time: string | null
  end_time: string | null
}

export interface BatchTask {
  task_id: string
  dataset_name: string
  total_cases: number
  cases: CaseResult[]
  status: 'pending' | 'processing' | 'completed' | 'failed'
  created_at: string | null
  started_at: string | null
  completed_at: string | null
  error: string | null
  progress: number
  current_step: string
  success: number
  failed: number
}

export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
}

/**
 * 上传数据集
 */
export async function uploadDataset(file: File): Promise<ApiResponse<DatasetInfo>> {
  const formData = new FormData()
  formData.append('file', file)

  return apiClient.post('/batch/datasets/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

/**
 * 获取数据集列表
 */
export async function listDatasets(): Promise<ApiResponse<DatasetInfo[]>> {
  return apiClient.get('/batch/datasets')
}

/**
 * 获取数据集详情
 */
export async function getDataset(datasetName: string): Promise<ApiResponse<DatasetInfo>> {
  return apiClient.get(`/batch/datasets/${datasetName}`)
}

/**
 * 删除数据集
 */
export async function deleteDataset(datasetName: string): Promise<ApiResponse<void>> {
  return apiClient.delete(`/batch/datasets/${datasetName}`)
}

/**
 * 创建批量执行任务
 */
export async function createBatchTask(params: {
  dataset_name: string
  selected_cases?: string[]
}): Promise<ApiResponse<BatchTask>> {
  return apiClient.post('/batch/execute', params)
}

/**
 * 获取批量任务状态
 */
export async function getBatchTask(taskId: string): Promise<ApiResponse<BatchTask>> {
  return apiClient.get(`/batch/tasks/${taskId}`)
}

/**
 * 获取批量任务列表
 */
export async function listBatchTasks(limit = 20): Promise<ApiResponse<BatchTask[]>> {
  return apiClient.get('/batch/tasks', { params: { limit } })
}

/**
 * 取消批量任务
 */
export async function cancelBatchTask(taskId: string): Promise<ApiResponse<void>> {
  return apiClient.post(`/batch/tasks/${taskId}/cancel`)
}

/**
 * 下载批量执行结果（ZIP）
 */
export function downloadBatchResults(taskId: string): string {
  return `/api/v1/batch/tasks/${taskId}/results`
}

/**
 * 下载批量执行报告（JSON）
 */
export function downloadBatchReport(taskId: string): string {
  return `/api/v1/batch/tasks/${taskId}/report`
}

/**
 * 预览case文件
 */
export async function previewCaseFile(
  taskId: string,
  caseName: string,
  fileType: 'json' | 'md'
): Promise<ApiResponse<{
  content: string
  size: number
  lines: number
  filename: string
  encoding: string
}>> {
  return apiClient.get(`/batch/tasks/${taskId}/cases/${caseName}/preview`, {
    params: { file_type: fileType }
  })
}

/**
 * 下载case文件
 */
export function downloadCaseFile(taskId: string, caseName: string, fileType: 'json' | 'md'): string {
  return `/api/v1/batch/tasks/${taskId}/cases/${caseName}/download?file_type=${fileType}`
}
